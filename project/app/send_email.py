import boto3
from botocore.exceptions import ClientError

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SENDER = "nsbharath@fipointer.com"
SENDERNAME = 'Sender Name'

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
RECIPIENT = "recipient@example.com"

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the
# ConfigurationSetName=CONFIGURATION_SET argument below.
CONFIGURATION_SET = "ConfigSet"

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = "us-east-1"

# The subject line for the email.
SUBJECT = "FiPointer Reports for {{date}}"

# The character encoding for the email.
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses', region_name=AWS_REGION)


async def send_email(recipient: str, uuid: str, full_name: str) -> None:
    # Try to send the email.
    print(uuid)
    template_data = '{ "name":"' + full_name + '" ,"uuid": "' + uuid + '"}'
    print(template_data)
    try:
        # Provide the contents of the email.
        response = client.send_templated_email(
            Source=SENDER,
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Template='TEMPLATE_NAME',
            TemplateData=template_data

            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return response['MessageId']
