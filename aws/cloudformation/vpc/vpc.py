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
from optparse import OptionParser
from troposphere import Base64, FindInMap, GetAtt, GetAZs, Join, Select, Tags
from troposphere import Output
from troposphere import Parameter, Ref, Template
import troposphere.ec2 as ec2


def add_content(template, environment, purpose):
    # Create parameters here since they must be passed to other functions.
    param_pem_key_name = template.add_parameter(
        Parameter(
            'PemKeyName',
            Description='The PEM key to use for this VPC.',
            Type='AWS::EC2::KeyPair::KeyName'
        )
    )

    add_description(template)

    add_version(template)

    name_region_attribute_map = 'RegionAttributeMap'
    add_mappings(template, name_region_attribute_map)

    add_resources(template, environment, purpose, name_region_attribute_map, param_pem_key_name)

def add_description(template):
    template.add_description('Creates a standard Virtual Private Cloud (VPC).')


def add_mappings(template, name_region_attribute_map):
    template.add_mapping(
        name_region_attribute_map,
        {
            # Amazon Linux AMI as f(region).
            # Chose the latest with virtualization type hvm.
            # Should review occasionally.
            'ap-southeast-1': {
                'BastionHostAmi': 'ami-1ddc0b7e'
            },
            'ap-southeast-2': {
                'BastionHostAmi': 'ami-0c95b86f'
            },
            'us-east-1': {
                'BastionHostAmi': 'ami-a4827dc9'
            },
            'us-west-1': {
                'BastionHostAmi': 'ami-11790371'
            }
        }
    )

def add_resources(template, environment, purpose, name_region_attribute_map, param_pem_key_name):
    # IP address for Seattle, Palmerston North, and Auckland offices. (Airport codes used as keys.)
    home_network_cidr_dict = dict((('Akl', '121.98.118.142/32'),
                                   ('Pmr', '121.99.230.178/32'),
                                   ('Sea', '67.131.4.94/30')))

    # PostgresSQL database port
    database_port_number = 5432

    # Create the VPC.
    cidr_block_vpc = '10.0.0.0/16'
    name_vpc = 'Vpc%s%s' % (purpose, environment)
    resource_vpc = ec2.VPC(
        name_vpc,
        CidrBlock=cidr_block_vpc,
        EnableDnsHostnames=True,
        Tags=Tags(Name=name_vpc, Purpose=purpose, Environment=environment),
    )
    template.add_resource(resource_vpc)
    template.add_output(
        Output('VPC',
               Description='VPC created for purpose: %s, environment: %s' % (purpose, environment),
               Value=Ref(resource_vpc)
        )
    )
    # Report the CIDR block of the VPC as an output.
    template.add_output(
        Output('VpcCidrBlock',
               Description='CIDR block of VPC',
               Value=cidr_block_vpc)
    )

    # Create the security group for the VPC.
    name_security_group_vpc = 'VpcSecurityGroup%s%s' % (purpose, environment)
    resource_security_group_vpc = ec2.SecurityGroup(
        name_security_group_vpc,
        GroupDescription=Join(' ', ['Security group for VPC', Ref(resource_vpc)]),
        Tags=Tags(Name=name_security_group_vpc, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_security_group_vpc)
    template.add_output(
        Output(
            'SecurityGroup',
            Description='Security group created for VPC.',
            Value=Ref(resource_security_group_vpc)
        )
    )

    # Add security group ingress rules.
    # ICMP from home networks.
    for site in home_network_cidr_dict.keys():
        template.add_resource(ec2.SecurityGroupIngress(
            'SecurityGroupIngressIcmp%s%s%s' % (purpose, environment, site),
            IpProtocol='icmp',
            FromPort='-1',
            ToPort='-1',
            CidrIp=home_network_cidr_dict[site],
            GroupId=Ref(resource_security_group_vpc)
        ))

    # ICMP from within the VPC.
    template.add_resource(ec2.SecurityGroupIngress(
        'SecurityGroupIngressVpcIcmp%s%s' % (purpose, environment),
        IpProtocol='icmp',
        FromPort='-1',
        ToPort='-1',
        CidrIp=cidr_block_vpc,
        GroupId=Ref(resource_security_group_vpc)
    ))

    # SSH from home networks
    for site in home_network_cidr_dict.keys():
        template.add_resource(ec2.SecurityGroupIngress(
            'SecurityGroupIngressSsh%s%s%s' % (purpose, environment, site),
            IpProtocol='tcp',
            FromPort='22',
            ToPort='22',
            CidrIp=home_network_cidr_dict[site],
            GroupId=Ref(resource_security_group_vpc)
        ))

    # SSH from within the VPC.
    template.add_resource(ec2.SecurityGroupIngress(
        'SecurityGroupIngressVpcSsh%s%s' % (purpose, environment),
        IpProtocol='tcp',
        FromPort='22',
        ToPort='22',
        CidrIp=cidr_block_vpc,
        GroupId=Ref(resource_security_group_vpc)
    ))

    # For dev environments, restrict http(s) to home networks.
    if environment.lower() == 'dev':
        # HTTP from home networks.
        for site in home_network_cidr_dict.keys():
            template.add_resource((ec2.SecurityGroupIngress(
                'SecurityGroupIngressHttp%s%s%s' % (purpose, environment, site),
                IpProtocol='tcp',
                FromPort='80',
                ToPort='80',
                CidrIp=home_network_cidr_dict[site],
                GroupId=Ref(resource_security_group_vpc)
            )))

        # HTTPS from home networks.
        for site in home_network_cidr_dict.keys():
            template.add_resource((ec2.SecurityGroupIngress(
                'SecurityGroupIngressHttps%s%s%s' % (purpose, environment, site),
                IpProtocol='tcp',
                FromPort='443',
                ToPort='443',
                CidrIp=home_network_cidr_dict[site],
                GroupId=Ref(resource_security_group_vpc)
            )))

    # For non-dev environments, open HTTP(s) to the internet.
    else:
        # HTTP from anywhere.
        template.add_resource(ec2.SecurityGroupIngress(
            'SecurityGroupIngressHttp%s%s' % (purpose, environment),
            IpProtocol='tcp',
            FromPort='80',
            ToPort='80',
            CidrIp='0.0.0.0/0',
            GroupId=Ref(resource_security_group_vpc)
        ))

        # HTTPS from anywhere.
        template.add_resource(ec2.SecurityGroupIngress(
            'SecurityGroupIngressHttps%s%s' % (purpose, environment),
            IpProtocol='tcp',
            FromPort='443',
            ToPort='443',
            CidrIp='0.0.0.0/0',
            GroupId=Ref(resource_security_group_vpc)
        ))

    # Add security group egress rules. (TBD)
    template.add_resource(ec2.SecurityGroupEgress(
        'SecurityGroupEgress%s%s' % (purpose, environment),
        IpProtocol='-1',
        FromPort='-1',
        ToPort='-1',
        CidrIp='0.0.0.0/0',
        GroupId=Ref(resource_security_group_vpc)
    ))

    # Create an internet gateway.
    name_internet_gateway = 'InternetGateway%s%s' % (purpose, environment)
    resource_internet_gateway = ec2.InternetGateway(
        name_internet_gateway,
        Tags=Tags(Name=name_internet_gateway, Purpose=purpose, Environment=environment),
    )
    template.add_resource(resource_internet_gateway)

    # Attach the internet gateway to the VPC.
    name_vpc_internet_gateway_attachment = 'VpcGatewayAttachment%s%s' % (purpose, environment)
    resource_internet_gateway_attachment = ec2.VPCGatewayAttachment(
        name_vpc_internet_gateway_attachment,
        VpcId=Ref(resource_vpc),
        InternetGatewayId=Ref(resource_internet_gateway)
    )
    template.add_resource(resource_internet_gateway_attachment)

    # Create a public and private subnet in two availability zones
    # for a total of four subnets.
    # TODO:  Get the subnet CIDR blocks correct, i.e.,
    # appropriately sized to anticipate future growth.
    # What is here now is just a SWAG.
    public_subnet_cidr_dict = dict(A='10.0.0.0/24', B='10.0.1.0/24')
    private_subnet_cidr_dict = dict(A1='10.0.10.0/24', B1='10.0.11.0/24')

    # Create public subnet A.
    name_subnet = 'SubnetPublicA%s%s' % (purpose, environment)
    resource_subnet_public_a = ec2.Subnet(
        name_subnet,
        AvailabilityZone=Select('0', GetAZs('')),
        CidrBlock=public_subnet_cidr_dict['A'],
        Tags=Tags(Name=name_subnet, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_subnet_public_a)
    template.add_output(
        Output(
            name_subnet,
            Description='Public Subnet A',
            Value=Ref(resource_subnet_public_a)
        )
    )

    # Create public subnet B.
    name_subnet = 'SubnetPublicB%s%s' % (purpose, environment)
    resource_subnet_public_b = ec2.Subnet(
        name_subnet,
        AvailabilityZone=Select('1', GetAZs('')),
        CidrBlock=public_subnet_cidr_dict['B'],
        Tags=Tags(Name=name_subnet, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_subnet_public_b)
    template.add_output(
        Output(
            name_subnet,
            Description='Public subnet B',
            Value=Ref(resource_subnet_public_b)
        )
    )

    # Create the private subnet A1.
    name_subnet = 'SubnetPrivateA1%s%s' % (purpose, environment)
    resource_subnet_private_a1 = ec2.Subnet(
        name_subnet,
        AvailabilityZone=Select('0', GetAZs('')),
        CidrBlock=private_subnet_cidr_dict['A1'],
        Tags=Tags(Name=name_subnet, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_subnet_private_a1)
    template.add_output(
        Output(
            name_subnet,
            Description='Private subnet A1',
            Value=Ref(resource_subnet_private_a1)
        )
    )

    # Create the private subnet B1.
    name_subnet = 'SubnetPrivateB1%s%s' % (purpose, environment)
    resource_subnet_private_b1 = ec2.Subnet(
        name_subnet,
        AvailabilityZone=Select('1', GetAZs('')),
        CidrBlock=private_subnet_cidr_dict['B1'],
        Tags=Tags(Name=name_subnet, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_subnet_private_b1)
    template.add_output(
        Output(
            name_subnet,
            Description='Private subnet B1',
            Value=Ref(resource_subnet_private_b1)
        )
    )

    # Subnets are created at this point.  Create dictionaries for iteration.
    public_subnet_resource_dict = dict(A=resource_subnet_public_a, B=resource_subnet_public_b)
    private_subnet_resource_dict = dict(A1=resource_subnet_private_a1, B1=resource_subnet_private_b1)

    # Create an Elastic IP for the NAT gateway.
    name_nat_eip = 'NatEip%s%s' % (purpose, environment)
    resource_nat_eip = ec2.EIP(
        name_nat_eip,
        Domain=name_vpc
    )
    template.add_resource(resource_nat_eip)

    # Create the NAT gateway in public subnet B.
    name_nat_gateway = 'NatGateway%s%s' % (purpose, environment)
    resource_nat_gateway = ec2.NatGateway(
        name_nat_gateway,
        AllocationId=GetAtt(name_nat_eip, 'AllocationId'),
        DependsOn=name_vpc_internet_gateway_attachment,
        SubnetId=Ref(resource_subnet_public_b),
    )
    template.add_resource(resource_nat_gateway)

    # Create the public subnet route table.
    name_route_table = 'RouteTablePublic%s%s' % (purpose, environment)
    resource_route_table_public = ec2.RouteTable(
        name_route_table,
        Tags=Tags(Name=name_route_table, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_route_table_public)

    # Add a route from the public subnets to the internet.
    template.add_resource(ec2.Route(
        'RouteToInternetPublicSubnets%s%s' % (purpose, environment),
        DependsOn=name_vpc_internet_gateway_attachment,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=Ref(resource_internet_gateway),
        RouteTableId=Ref(resource_route_table_public),
    ))

    # Associate the route table with the AZ-A, AZ-B subnets.
    for subnet in public_subnet_resource_dict.keys():
        template.add_resource(ec2.SubnetRouteTableAssociation(
            'RouteTableAssocPublicSubnet%s%s%s' % (subnet, purpose, environment),
            RouteTableId=Ref(resource_route_table_public),
            SubnetId=Ref(public_subnet_resource_dict[subnet])
        ))

    # Create the private subnet route table.
    name_route_table = 'RouteTablePrivate%s%s' % (purpose, environment)
    resource_route_table_private = ec2.RouteTable(
        name_route_table,
        Tags=Tags(Name=name_route_table, Purpose=purpose, Environment=environment),
        VpcId=Ref(resource_vpc)
    )
    template.add_resource(resource_route_table_private)

    # Add route to internet via NAT.
    template.add_resource(ec2.Route(
        'RouteToInternetPrivateSubnet%s%s' % (purpose, environment),
        DependsOn=name_vpc_internet_gateway_attachment,
        DestinationCidrBlock='0.0.0.0/0',
        NatGatewayId=Ref(resource_nat_gateway),
        RouteTableId=Ref(resource_route_table_private)
    ))

    # Associate the route table with the AZ-A1, AZ-B1 subnets.
    for subnet in private_subnet_resource_dict.keys():
        template.add_resource(ec2.SubnetRouteTableAssociation(
            'RouteTableAssocPrivateSubnet%s%s%s' % (subnet, purpose, environment),
            RouteTableId=Ref(resource_route_table_private),
            SubnetId=Ref(private_subnet_resource_dict[subnet])
        ))

    # Create the bastion host.
    name_bastion_host = 'BastionHost%s%s' % (purpose, environment)
    resource_bastion_host = ec2.Instance(
        name_bastion_host,
        DependsOn=name_vpc_internet_gateway_attachment,
        ImageId=FindInMap(name_region_attribute_map, Ref('AWS::Region'), 'BastionHostAmi'),
        InstanceType='t2.micro',
        KeyName=Ref(param_pem_key_name),
        NetworkInterfaces=[
            ec2.NetworkInterfaceProperty(
                AssociatePublicIpAddress=str(True),
                DeleteOnTermination=str(True),
                Description='Bastion host network interface for %s%s' % (purpose, environment),
                DeviceIndex=str(0),
                GroupSet=[Ref(resource_security_group_vpc)],
                SubnetId=Ref(resource_subnet_public_a),
            )
        ],
        Tags=Tags(Name=name_bastion_host, Purpose=purpose, Environment=environment),
        UserData=Base64('80')
    )
    template.add_resource(resource_bastion_host)
    template.add_output(
        Output(
            name_bastion_host,
            Description='Bastion Host Public IP address',
            Value=GetAtt(resource_bastion_host, 'PublicIp')
        )
    )

def add_version(template):
    template.add_version(version='2010-09-09')


# ---Generate CloudFormation template------------------------------------------
def main():
    option_parser = OptionParser()

    option_parser.add_option(
        '-e', '--Environment',
        dest='environment',
        help='The environment (Prod, Stage, Dev) for which this script should generate content.',
        default='Dev'
    )

    option_parser.add_option(
        '-p', '--Purpose',
        dest='purpose',
        help='The purpose for which the resultant VPC will be used.',
        default='Platform'
    )

    (options, args) = option_parser.parse_args()
    environment = options.environment
    purpose = options.purpose
    template_path = './Vpc%s%s.json' % (purpose, environment)

    template = Template()

    add_content(template, environment, purpose)

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
