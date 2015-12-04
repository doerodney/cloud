# This script generates CloudFormation JSON with the troposphere library.
# Advantages:  Clean, allows comments in code, examples included.
# Disadvantages:  JSON section implemented alphabetical order,
# not in 'traditional' order.  (Order is irrelevant in JSON.)
# To use troposphere:
# Install python 2.7.10 or later
# The pip utility is in Python27/Scripts.
# pip install troposphere
# pip install awacs
# To get examples (highly useful):
# mkdir /github (or where you prefer)
# cd github
# mkdir cloudtools
# cd cloudtools
# git clone https://github.com/cloudtools/troposphere.git
# Optional but helpful:  Install PyCharm Community Edition (Cost=0)
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Output, Parameter, Ref, Template
import troposphere.ec2 as ec2

out_path = './jenkins_linux_simple.json'

template = Template()

#---Parameters-----------------------------------------------------------------
param_keyname = template.add_parameter(
    Parameter(
        'KeyName',
        Description='Name of an existing EC2 KeyPair file (.pem) to use to create EC2 instances',
        Type='AWS::EC2::KeyPair::KeyName'
    )
)

param_instance_type = template.add_parameter(
    Parameter(
        'EC2InstanceType',
        Description='EC2 instance type, reference this parameter to insure consistency',
        Type='String',
        Default='t2.micro',
        AllowedValues=[
            't2.small',
            't2.micro',
            't2.medium',
            't2.large',
            'm3.medium',
            'm3.large'
        ],
        ConstraintDescription='Must be a valid EC2 instance type'
    )
)

param_environment = template.add_parameter(
    Parameter(
        'Environment',
        Description='The environment name with which to associate this.',
        Type='String',
        AllowedValues=[
            'TestAws',
            'Dev',
            'DevOps'
        ],
        Default='DevOps'
    )
)

#---Mappings-------------------------------------------------------------------
mapping_region_map = template.add_mapping(
    'RegionMap',
    {
        'ap-northeast-1': {
            'AMI': 'ami-383c1956',
            'RegionAvailabilityZone': 'ap-northeast-1c'
        },
        'ap-southeast-1': {
            'AMI': 'ami-c9b572aa',
            'RegionAvailabilityZone': 'ap-southeast-1b'
        },
        'ap-southeast-2': {
            'AMI': 'ami-48d38c2b',
            'RegionAvailabilityZone': 'ap-southeast-2b'
        },
        'eu-central-1': {
            'AMI': 'ami-bc5b48d0',
            'RegionAvailabilityZone': 'eu-central-1b'
        },
        'eu-west-1': {
            'AMI': 'ami-bff32ccc',
            'RegionAvailabilityZone': 'eu-west-1c'
        },
        'sa-east-1': {
            'AMI': 'ami-6817af04',
            'RegionAvailabilityZone': 'sa-east-1c'
        },
        'us-east-1': {
            'AMI': 'ami-60b6c60a',
            'RegionAvailabilityZone': 'us-east-1e'
        },
        'us-west-1': {
            'AMI': 'ami-d5ea86b5',
            'RegionAvailabilityZone': 'us-west-1c'
        },
        'us-west-2': {
            'AMI': 'ami-f0091d91',
            'RegionAvailabilityZone': 'us-west-2c'
        }
    }
)

#---Resources------------------------------------------------------------------
# Allow SSH, http, https, and Jenkins on 8080
jenkins_linux_security_group = template.add_resource(ec2.SecurityGroup(
        'JenkinsLinuxSecurityGroup',
        GroupDescription='Security Group for Jenkins on Linux.',
        SecurityGroupIngress=
        [
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort=22,
                ToPort=22,
                CidrIp='0.0.0.0/0'
            ),
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort=80,
                ToPort=80,
                CidrIp='0.0.0.0/0'
            ),
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort=443,
                ToPort=443,
                CidrIp='0.0.0.0/0'
            ),
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort=8080,
                ToPort=8080,
                CidrIp='0.0.0.0/0'
            )
        ]
    )
)

ec2_instance = template.add_resource(ec2.Instance
    (
        'EC2Instance',
        ImageId=FindInMap('RegionMap', Ref('AWS::Region'), 'AMI'),
        InstanceType=Ref(param_instance_type),
        KeyName=Ref(param_keyname),
        SecurityGroups=[Ref(jenkins_linux_security_group)],
        UserData=Base64(Join('',
                [
                    '#!/bin/bash -ex \n',
                    'y      um -y install java \n',
                    'wget -O /etc/yum.repos.d/jenkins.repo http://pkg.jenkins-ci.org/redhat/jenkins.repo \n',
                    'rpm --import https://jenkins-ci.org/redhat/jenkins-ci.org.key \n',
                    'yum -y install jenkins \n',
                    'service jenkins start \n',
                    'chkconfig jenkins on \n'
                ]
            )
        )
    )
)

#---Outputs--------------------------------------------------------------------
template.add_output(Output(
        'JenkinsURL',
        Description='URL of the Jenkins instance.',
        Value=Join('',
            [
                'http://',
                GetAtt(ec2_instance, 'PublicIp'),
                ':8080'
            ]
        )
    )
)

template.add_output(Output(
        'Region',
        Description='AWS Region used for instantiation',
        Value=Ref('AWS::Region')

    )
)

template.add_output(Output(
        'AvailabilityZone',
        Description='Availability zone used with AWS region',
        Value=FindInMap('RegionMap', Ref('AWS::Region'), 'RegionAvailabilityZone')
    )
)

template.add_output(Output(
        'Environment',
        Description='Value of the Environment parameter',
        Value=Ref(param_environment)
    )
)

#---Generate CloudFormation template-------------------------------------------
# Generate JSON.
json = template.to_json()

# Write JSON to console.
print json

# Write JSON to a file.
file = open(out_path, mode='w')
file.writelines(json)
file.close()

print 'Generated CloudFormation template is available in %s' % out_path