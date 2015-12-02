from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Output, Parameter, Ref, Template
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, Tag
from troposphere.elasticloadbalancing import LoadBalancer
import troposphere.elasticloadbalancing as elb
import troposphere.ec2 as ec2

out_path = './WebAuthor.json'

template = Template()

#---Description----------------------------------------------------------------
template.add_description("""Configures an autoscaling group for WebAuthor (AKA Huxley)""")

#---Version--------------------------------------------------------------------
template.add_version(version='2010-09-09')

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
            'Corp',
            'Dev',
            'Prod'
        ],
        Default='Dev'
    )
)

#---Mappings-------------------------------------------------------------------
# Get Windows Server 2012 AMI as f(region).
mapping_region_map = template.add_mapping(
    'RegionMap',
    {
        'ap-northeast-1': {
            'AMI': 'ami-3e93fe3e'
        },
        'ap-southeast-1': {
            'AMI': 'ami-faedfea8'
        },
        'ap-southeast-2': {
            'AMI': 'ami-7bda9041'
        },
        'eu-central-1': {
            'AMI': 'ami-f2f5f9ef'
        },
        'eu-west-1': {
            'AMI': 'ami-2fcbf458'
        },
        'sa-east-1': {
            'AMI': 'ami-02952d6e'
        },
        'us-east-1': {
            'AMI': 'ami-1df0ac78'
        },
        'us-west-1': {
            'AMI': 'ami-91f93ad5'
        },
        'us-west-2': {
            'AMI': 'ami-xxxxxxxx'
        }
    }
)

# Map attributes to environment.
mapping_environment_attribute_map = template.add_mapping(
    'EnvironmentAttributeMap',
    {
        'Corp': {
            'VpcId': 'vcp-xxxxxxxx',
            'PublicSubnetArray': ['subnet-xxxxxxxx','subnet-xxxxxxxx'],
            'SSLCertificateId': 'arn:aws:iam::724037942444:server-certificate/GodaddyChainCert'
        },
        'Dev': {
            'VpcId': 'vpc-79af551c',
            'PublicSubnetArray': ['subnet-054e9c60','subnet-0fbcae49'],
            'SSLCertificateId': 'arn:aws:iam::724037942444:server-certificate/GodaddyChainCert'
        },
        'Prod': {
            'VpcId': 'vcp-xxxxxxxx',
            'PublicSubnetArray': ['subnet-xxxxxxxx','subnet-xxxxxxxx'],
            'SSLCertificateId': 'arn:aws:iam::724037942444:server-certificate/GodaddyChainCert'
        }
    }
)

#---Resources------------------------------------------------------------------
# Allow SSH, http, https, and Jenkins on 8080
load_balancer_security_group = template.add_resource(ec2.SecurityGroup(
        'WebAuthorLoadBalancerSecurityGroup',
        GroupDescription='Security Group for WebAuthor (Windows).',
        SecurityGroupIngress=
        [
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
            )
        ],
        VpcId=FindInMap('EnvironmentAttributeMap', Ref(param_environment), 'VpcId'),
    )
)

load_balancer = template.add_resource(LoadBalancer(
        'WebAuthorLoadBalancer',
        ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
            Enabled=True,
            Timeout=120
        ),
        CrossZone=True,

        HealthCheck=elb.HealthCheck(
            Target='HTTP:80/',
            HealthyThreshold='5',
            UnhealthyThreshold='2',
            Interval='20',
            Timeout='15',
        ),
        Listeners=[
            elb.Listener(
                LoadBalancerPort='443',
                InstancePort='80',
                Protocol='HTTPS',
                InstanceProtocol='HTTP',
                SSLCertificateId=FindInMap('EnvironmentAttributeMap', Ref(param_environment), 'SSLCertificateId')
            )
        ],
        LoadBalancerName='WebAuthorLoadBalancer',
        SecurityGroups=[Ref('WebAuthorLoadBalancerSecurityGroup')],
        Scheme='internet-facing',
        Subnets=FindInMap('EnvironmentAttributeMap', Ref(param_environment), 'PublicSubnetArray')
    )
)

launch_configuration = template.add_resource(LaunchConfiguration(
        'WebAuthorLaunchConfiguration',
        ImageId=FindInMap('RegionMap', Ref('AWS::Region'), 'AMI'),
        InstanceType=Ref(param_instance_type),
        KeyName=Ref(param_keyname),
        SecurityGroups=[Ref(load_balancer_security_group)]
    )
)

autoscaling_group = template.add_resource(AutoScalingGroup(
        'WebAuthorAutoscalingGroup',
        DesiredCapacity=2,
        HealthCheckGracePeriod=300,
        HealthCheckType='EC2',
        LaunchConfigurationName=Ref(launch_configuration),
        LoadBalancerNames=[Ref(load_balancer)],
        MaxSize=2,
        MinSize=2,
        Tags=[
            Tag('Purpose', 'WebAuthor', True),
            Tag('Environment', Ref(param_environment), True)
        ],
        VPCZoneIdentifier=FindInMap('EnvironmentAttributeMap', Ref(param_environment), 'PublicSubnetArray')
    )
)

#---Outputs--------------------------------------------------------------------
template.add_output(Output(
        'LoadBalancerCanonicalHostedZoneName',
        Description='The name of the Amazon Route 53 hosted zone that is associated with the load balancer.',
        Value=GetAtt(load_balancer, 'CanonicalHostedZoneName')
    )
)

template.add_output(Output(
        'LoadBalancerCanonicalHostedZoneNameID',
        Description='The ID of the Route 53 hosted zone name that is associated with the load balancer.',
        Value=GetAtt(load_balancer, 'CanonicalHostedZoneNameID')
    )
)

template.add_output(Output(
        'DNSName',
        Description='The DNS name for the load balancer.',
        Value=GetAtt(load_balancer, 'DNSName')
    )
)

template.add_output(Output(
        'AWSRegion',
        Description='AWS Region used for instantiation',
        Value=Ref('AWS::Region')
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