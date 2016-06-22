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
from troposphere import Base64, FindInMap, GetAtt, Join, Tags
from troposphere import Output
from troposphere import Parameter, Ref, Template
import troposphere.cloudformation as cloudformation
import troposphere.ec2 as ec2


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

    param_vpc_security_group = Parameter(
        'VpcSecurityGroup',
        Description='The security group (sg-abcdwxyz) to apply to the resources created by this stack.',
        Type='AWS::EC2::SecurityGroup::Id',
    )
    template.add_parameter(param_vpc_security_group)

    param_webserver_instance_subnet_id = Parameter(
        'VpcSubnetIdentifer',
        Description='The identity of the public subnet (subnet-abcdwxyz) in which the web server shall be created.',
        Type='AWS::EC2::Subnet::Id',
    )
    template.add_parameter(param_webserver_instance_subnet_id)

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


    #---Mappings---------------------------------------------------------------
    mapping_environment_attribute_map = template.add_mapping(
        'EnvironmentAttributeMap',
        {
            'ap-southeast-1': {
                'WebServerAmi': 'ami-1ddc0b7e'
            },
            'ap-southeast-2': {
                'WebServerAmi': 'ami-0c95b86f'
            },
            'us-east-1': {
                'WebServerAmi': 'ami-a4827dc9'
            },
            'us-west-1': {
                'WebServerAmi': 'ami-f5f41398'
            }
        }
    )

    # ---Resources-------------------------------------------------------------
    ref_region = Ref('AWS::Region')
    ref_stack_name = Ref('AWS::StackName')

    # Create the metadata for the server instance.
    name_web_server = 'WebServer'
    webserver_instance_metadata = cloudformation.Metadata(
        cloudformation.Init({
            'config': cloudformation.InitConfig(
                packages={
                    'yum': {
                        'nginx': [],
                        'git': []
                    }
                },
                files=cloudformation.InitFiles({
                    # cfn-hup.conf initialization
                    '/etc/cfn/authorapp.conf': cloudformation.InitFile(
                        content=Join('',
                        [
                            'server {', '\n',
                            '	listen 3030 ssl http2;', '\n',
                            '	root /var/www/authorapp;', '\n',
                            '\n',
                            '	ssl_certificate       /vagrant/ssl/ca.crt;', '\n',
                            '	ssl_certificate_key   /vagrant/ssl/ca.key;', '\n',
                            '\n',
                            '	location / {', '\n',
                            '	}', '\n',
                            '\n',
                            '	location /api {', '\n',
                            '		proxy_pass http://10.50.50.1:3000;', '\n',
                            '	}', '\n',
                            '}', '\n',
                        ]),
                        mode='000400',
                        owner='root',
                        group='root'
                    ),

                }),
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
                            # Disable sendmail service - not required.
                            'sendmail': cloudformation.InitService(
                                enabled=False,
                                ensureRunning=False
                            )
                        }
                    )
                )
            )
        })
    )

    resource_web_server = ec2.Instance(
        name_web_server,
        Metadata=webserver_instance_metadata,
        ImageId=FindInMap('EnvironmentAttributeMap', ref_region, 'WebServerAmi'),
        InstanceType=Ref(param_instance_type),
        KeyName=Ref(param_keyname),
        NetworkInterfaces=[
            ec2.NetworkInterfaceProperty(
                AssociatePublicIpAddress=str(True),
                DeleteOnTermination=str(True),
                Description='Network interface for web server',
                DeviceIndex=str(0),
                GroupSet=[Ref(param_vpc_security_group)],
                SubnetId=Ref(param_webserver_instance_subnet_id),
            )
        ],
        Tags=Tags(Name=name_web_server, VPC=Ref(param_vpc_id)),
        UserData=Base64(
            Join(
                '',
                [
                    '#!/bin/bash -xe\n',
                    'yum update -y aws-cfn-bootstrap\n',

                    'yum update -y', '\n'

                    '/opt/aws/bin/cfn-init --verbose ',
                    ' --stack ', ref_stack_name,
                    ' --resource %s ' % name_web_server,
                    ' --region ', ref_region, '\n',

                    '/opt/aws/bin/cfn-signal --exit-code $? ',
                    ' --stack ', ref_stack_name,
                    ' --resource ',
                    name_web_server,
                    '\n'
                ]
            )
        )
    )
    template.add_resource(resource_web_server)
    template.add_output(
        Output('WebServer',
               Description='Web Server',
               Value=GetAtt(name_web_server, 'PublicIp')
        )
    )

    return template

# ---Generate CloudFormation template------------------------------------------
def main():
    template_path = './ClientStack.json'

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