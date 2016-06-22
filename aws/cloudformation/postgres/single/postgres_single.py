# This script generates CloudFormation JSON with the troposphere library.
# Advantages:  Clean, allows comments in code, examples included.
# Disadvantages:  JSON section implemented alphabetical order,
# not in 'traditional' order.  (Order is irrelevant in JSON.)
# To use troposphere:
# Install python 2.7.10 or later
# The pip utility is in Python27/Scripts.
# pip install troposphere
# pip install awacs
# This script uses the boto3 library to get build versions from S3.
# pip install boto3
# Optional but quite helpful:  Install PyCharm Community Edition (Cost=0)
from troposphere import Base64, FindInMap, Join, Tags
from troposphere import Output
from troposphere import Parameter, Ref, Template
import troposphere.cloudformation as cloudformation
import troposphere.ec2 as ec2
from awacs.aws import (Allow,
                       Statement,
                       Principal,
                       Policy)
from awacs.sts import AssumeRole
import troposphere.iam as iam

def generate_description(template):
    template.add_description('Creates a single instance of a PostgreSql server')

def generate_version(template):
    template.add_version(version='2010-09-09')

def generate_stack_template():
    template = Template()

    generate_description(template)

    generate_version(template)

    # ---Parameters------------------------------------------------------------
    param_vpc_id = Parameter(
        'VpcIdentifer',
        Description='The identity of the VPC (vpc-abcdwxyz) in which this stack shall be created.',
        Type='AWS::EC2::VPC::Id',
    )
    template.add_parameter(param_vpc_id)

    param_vpc_cidr_block = Parameter(
        'VpcCidrBlock',
        Description='The CIDR block of the VPC (w.x.y.z/n) in which this stack shall be created.',
        Type='String',
        Default='10.0.0.0/16'
    )
    template.add_parameter(param_vpc_cidr_block)

    param_database_instance_subnet_id = Parameter(
        'VpcSubnetIdentifer',
        Description='The identity of the private subnet (subnet-abcdwxyz) in which the database server shall be created.',
        Type='AWS::EC2::Subnet::Id',
    )
    template.add_parameter(param_database_instance_subnet_id)

    param_keyname = Parameter(
        'PemKeyName',
        Description='Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances',
        Type='AWS::EC2::KeyPair::KeyName'
    )
    template.add_parameter(param_keyname)

    param_instance_type = Parameter(
        'EC2InstanceType',
        Description='EC2 instance type, reference this parameter to insure consistency',
        Type='String',
        Default='t2.medium',  # Prices from (2015-12-03) (Windows, us-west (North CA))
        AllowedValues=[  # Source :  https://aws.amazon.com/ec2/pricing/
            't2.small',  # $0.044/hour
            't2.micro',  # $0.022/hour
            't2.medium',  # $0.088/hour
            't2.large',  # $0.166/hour
            'm3.medium',  # $0.140/hour
            'm3.large',  # $0.28/hour
            'c4.large'   # $0.221/hour
        ],
        ConstraintDescription='Must be a valid EC2 instance type'
    )
    template.add_parameter(param_instance_type)

    param_s3_bucket = Parameter(
        'S3Bucket',
        Description='The bucket in which applicable content can be found.',
        Type='String',
        Default='author-it-deployment-test-us-east-1'
    )
    template.add_parameter(param_s3_bucket)

    param_s3_key = Parameter(
        'S3Key',
        Description='The key within the bucket in which relevant files are located.',
        Type='String',
        Default='source/database/postgresql/single'
    )
    template.add_parameter(param_s3_key)

    param_database_admin_password = Parameter(
        'PostgresAdminPassword',
        Description='The password to be used by user postgres.',
        Type='String',
        NoEcho=True
    )
    template.add_parameter(param_database_admin_password)

    #---Mappings---------------------------------------------------------------
    mapping_environment_attribute_map = template.add_mapping(
        'EnvironmentAttributeMap',
        {
            'ap-southeast-1': {
                'DatabaseServerAmi': 'ami-1ddc0b7e'
            },
            'ap-southeast-2': {
                'DatabaseServerAmi': 'ami-0c95b86f'
            },
            'us-east-1': {
                'DatabaseServerAmi': 'ami-a4827dc9'
            },
            'us-west-1': {
                'DatabaseServerAmi': 'ami-f5f41398'
            }
        }
    )

    # ---Resources-------------------------------------------------------------
    ref_stack_id = Ref('AWS::StackId')
    ref_region = Ref('AWS::Region')
    ref_stack_name = Ref('AWS::StackName')
    path_database_admin_script = 'usr/ec2-user/postgresql/set_admin_password.sql'
    name_database_server_wait_handle = 'DatabaseServerWaitHandle'

    cmd_postgresql_initdb = dict(
        command='service postgresql-95 initdb'
    )

    cmd_start_postgresql_service = dict(
        command='service postgresql-95 start'
    )

    cmd_set_postgres_user_password = dict(
        command='psql -U postgres -f %s' % path_database_admin_script
    )

    cmd_start_postgresql_on_startup = dict(
        command='chkconfig postgresql on'
    )

    cmd_signal_success = dict(
        command='cfn-signal --exit-code $?'
    )

    # Create an instance of AWS::IAM::Role for the instance.
    # This allows:
    # - Access to S3 bucket content.
    # - Stack updates
    resource_instance_role = template.add_resource(iam.Role(
        'InstanceRole',
        AssumeRolePolicyDocument=Policy(
            Statement=[
                Statement(
                    Action=[AssumeRole],
                    Effect=Allow,
                    Principal=Principal(
                        'Service', ['ec2.amazonaws.com']
                    )
                )
            ]
        ),
        Path='/'
    ))

    # Create the S3 policy and attach it to the role.
    template.add_resource(iam.PolicyType(
        'InstanceS3DownloadPolicy',
        PolicyName='S3Download',
        PolicyDocument={
            'Statement':[
                {
                    'Effect': 'Allow',
                    'Action': ['s3:GetObject'],
                    'Resource': Join('', [
                        'arn:aws:s3:::',
                        Ref(param_s3_bucket),
                        '/*'
                    ])
                },
                {
                    'Effect': 'Allow',
                    'Action': ['cloudformation:DescribeStacks', 'ec2:DescribeInstances'],
                    'Resource': '*'
                }
            ]
        },
        Roles=[Ref(resource_instance_role)]
    ))

    # Create the CloudFormation stack update policy and attach it to the role.
    template.add_resource(iam.PolicyType(
        'InstanceStackUpdatePolicy',
        PolicyName='StackUpdate',
        PolicyDocument={
            'Statement':[
                {
                    "Effect" : "Allow",
                    "Action" : "Update:*",
                    "Resource" : "*"
                }
            ]
        },
        Roles=[Ref(resource_instance_role)]
    ))

    # Create the AWS::IAM::InstanceProfile from the role for reference in the
    # database server instance definition.
    resource_instance_profile = template.add_resource(iam.InstanceProfile(
        'InstanceProfile',
        Path='/',
        Roles=[Ref(resource_instance_role)]
    ))


    # Create a security group for the postgresql instance.
    # This must be internal to the VPC only.
    name_security_group_database = 'VpcDatabaseSecurityGroup'
    resource_database_security_group = ec2.SecurityGroup(
        name_security_group_database,
        GroupDescription=Join(' ', ['Security group for VPC database', Ref(param_vpc_id)]),
        Tags=Tags(Name=name_security_group_database),
        VpcId=Ref(param_vpc_id)
    )
    template.add_resource(resource_database_security_group)

    template.add_output(
        Output(
            'SecurityGroupForDatabase',
            Description='Security group created for database in VPC.',
            Value=Ref(resource_database_security_group)
        )
    )

    # Add ingress rule from VPC to database security group for database traffic.
    database_port = 5432
    ssh_port = 22
    template.add_resource(ec2.SecurityGroupIngress(
        'DatabaseSecurityGroupDatabaseIngress',
        CidrIp=Ref(param_vpc_cidr_block),
        FromPort=str(database_port),
        GroupId=Ref(resource_database_security_group),
        IpProtocol='tcp',
        ToPort=str(database_port)
    ))

    # Add ingress rule from VPC to database security group for ssh traffic.
    ssh_port = 22
    template.add_resource(ec2.SecurityGroupIngress(
        'DatabaseSecurityGroupSshIngress',
        CidrIp=Ref(param_vpc_cidr_block),
        FromPort=str(ssh_port),
        GroupId=Ref(resource_database_security_group),
        IpProtocol='tcp',
        ToPort=str(ssh_port)
    ))

    # Create the metadata for the database instance.
    name_database_server = 'DatabaseServer'
    database_instance_metadata = cloudformation.Metadata(
        cloudformation.Init({
            'config': cloudformation.InitConfig(
                packages={
                    'rpm': {
                        'postgresql': 'https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-6-x86_64/pgdg-ami201503-95-9.5-2.noarch.rpm'
                    },
                    'yum': {
                        'postgresql95': [],
                        'postgresql95-libs': [],
                        'postgresql95-server': [],
                        'postgresql95-devel': [],
                        'postgresql95-contrib': [],
                        'postgresql95-docs': []
                    }
                },
                files=cloudformation.InitFiles({
                    # cfn-hup.conf initialization
                    '/etc/cfn/cfn-hup.conf': cloudformation.InitFile(
                        content=Join('',
                        [
                            '[main]\n',
                            'stack=', ref_stack_id, '\n',
                            'region=', ref_region, '\n',
                            'interval=2', '\n',
                            'verbose=true', '\n'

                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),
                    # cfn-auto-reloader.conf initialization
                    '/etc/cfn/cfn-auto-reloader.conf': cloudformation.InitFile(
                        content=Join('', [
                            '[cfn-auto-reloader-hook]\n',
                            'triggers=post.update\n',
                            'path=Resources.%s.Metadata.AWS::CloudFormation::Init\n' % name_database_server,
                            'action=cfn-init.exe ',
                            ' --verbose '
                            ' --stack ', ref_stack_name,
                            ' --resource %s ' % name_database_server,  # resource that defines the Metadata
                            ' --region ', ref_region, '\n'
                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),
                    #
                    # pg_hba.conf retrieval from S3
                    '/var/lib/pgsql9/data/pg_hba.conf': cloudformation.InitFile(
                        source=Join('/', [
                            # Join('', ['https://s3-', ref_region, '.', 'amazonaws.com']),
                            'https://s3.amazonaws.com',
                            Ref(param_s3_bucket),
                            Ref(param_s3_key),
                            'conf'
                            'pg_hba.conf'
                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),
                    # postgresql.conf retrieval from S3
                    '/var/lib/pgsql9/data/postgresql.conf': cloudformation.InitFile(
                        source=Join('/', [
                            #Join('', ['https://s3-', ref_region, '.', 'amazonaws.com']),
                            'https://s3.amazonaws.com',
                            Ref(param_s3_bucket),
                            Ref(param_s3_key),
                            'conf'
                            'postgresql.conf'
                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),
                    # pg_ident.conf retrieval from S3
                    '/var/lib/pgsql9/data/pg_ident.conf': cloudformation.InitFile(
                        source=Join('/', [
                            #Join('', ['https://s3-', ref_region, '.', 'amazonaws.com']),
                            'https://s3.amazonaws.com',
                            Ref(param_s3_bucket),
                            Ref(param_s3_key),
                            'conf'
                            'pg_ident.conf'
                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),
                    # script to set postgresql admin password.
                    # (admin user = 'postgres')
                    path_database_admin_script: cloudformation.InitFile(
                        source=Join('', [
                            'ALTER USER postgres WITH PASSWORD ',
                            Ref(param_database_admin_password),
                            ';',
                            '\n'
                        ])
                    )
                }),
                commands={
                    '10-postgresql_initdb': cmd_postgresql_initdb,
                    '20-start_postgresql_service': cmd_start_postgresql_service,
                    '30-set-postgres-user-password': cmd_set_postgres_user_password,
                    '40-start-postgresql-on-startup': cmd_start_postgresql_on_startup,
                    #'99-signal-success': cmd_signal_success
                },
                services=dict(
                    sysvinit=cloudformation.InitServices(
                        {
                            # start cfn-hup service -
                            # required for CloudFormation stack update
                            'cfn-hup': cloudformation.InitService(
                                enabled=True,
                                ensureRunning=True,
                                files=[
                                    '/etc/cfn/cfn-hup.conf',
                                    '/etc/cfn/hooks.d/cfn-auto-reloader.conf'
                                ]
                            ),
                            # start postgresql service
                            'postgresql-9.5': cloudformation.InitService(
                                enabled=True,
                                ensureRunning=True
                            ),
                            # Disable sendmail service - not required.
                            'sendmail': cloudformation.InitService(
                                enabled=False,
                                ensureRunning=False
                            )
                        }
                    )
                )
            )
        }),
        cloudformation.Authentication({
            'S3AccessCredentials': cloudformation.AuthenticationBlock(
                buckets=[Ref(param_s3_bucket)],
                roleName=Ref(resource_instance_role),
                type='S3'
            )
        })
    )


    # Add a wait handle to receive the completion signal.
    #resource_database_server_wait_handle = template.add_resource(
    #    cloudformation.WaitConditionHandle(
    #        name_database_server_wait_handle
    #    )
    # )

    #template.add_resource(
    #    cloudformation.WaitCondition(
    #        'DatabaseServerWaitCondition',
    #        DependsOn=name_database_server,
    #        Handle=Ref(resource_database_server_wait_handle),
    #        Timeout=300,
    #    )
    #)

    resource_database_server = ec2.Instance(
        name_database_server,
        DependsOn=name_security_group_database,
        IamInstanceProfile=Ref(resource_instance_profile),
        Metadata=database_instance_metadata,
        ImageId=FindInMap('EnvironmentAttributeMap', ref_region, 'DatabaseServerAmi'),
        InstanceType=Ref(param_instance_type),
        KeyName=Ref(param_keyname),
        SecurityGroupIds=[Ref(resource_database_security_group)],
        SubnetId=Ref(param_database_instance_subnet_id),
        Tags=Tags(Name=name_database_server, VPC=Ref(param_vpc_id)),
        UserData=Base64(
            Join(
                '',
                [
                    '#!/bin/bash -xe\n',
                    'yum update -y aws-cfn-bootstrap\n',

                    '/opt/aws/bin/cfn-init --verbose ',
                    ' --stack ', ref_stack_name,
                    ' --resource DatabaseServer ',
                    ' --region ', ref_region, '\n',

                    '/opt/aws/bin/cfn-signal --exit-code $? ',
                    ' --stack ', ref_stack_name,
                    ' --resource ',
                    name_database_server,
                    '\n'
                ]
            )
        )
    )
    template.add_resource(resource_database_server)
    template.add_output(
        Output('DatabaseServer',
               Description='PostgreSQL single instance database server',
               Value=Ref(resource_database_server)
        )
    )

    return template

# ---Generate CloudFormation template------------------------------------------
def main():
    template_path = './PostgresqlSingleInstanceStack.json'

    template = generate_stack_template()

    # Generate JSON.
    json = template.to_json()
    # Write JSON to console.
    print json

    # Write JSON to a file.
    file = open(template_path, mode='w')
    file.writelines(json)
    file.close()

    print 'Generated CloudFormation template is available in %s' % template_path

if __name__ == '__main__':
    main()