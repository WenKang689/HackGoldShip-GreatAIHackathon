import boto3
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-5')
table = dynamodb.Table('hackathon-invoice')

# Mock data
customers = [
 'Emily Zhang', 'Jason Lim', 'Chloe Tan', 'Daniel Lee', 'Sophia Chen', 'Ryan Wong', 'Isabella Tan', 'Joshua Ong',
 'Nicholas Chua', 'Grace Ho', 'Benjamin Lau', 'Victoria Yeo', 'Ethan Koh', 'Olivia Goh', 'Samuel Teo', 'Hannah Lim',
 'Jonathan Tan', 'Megan Ong', 'Christopher Lee', 'Ashley Wong', 'Matthew Chen', 'Rachel Lim', 'Andrew Ng', 'Jessica Tan',
 'Brandon Chua', 'Nicole Yeo', 'Justin Goh', 'Alicia Ho', 'Marcus Lau', 'Fiona Teo', 'Alexander Lim', 'Samantha Lee',
 'Jeremy Wong', 'Clara Tan', 'Sean Chen', 'Melissa Ong', 'Darren Ng', 'Vanessa Ho', 'Adrian Teo', 'Sabrina Lau',
 'Patrick Goh', 'Irene Chua', 'Kelvin Tan', 'Serena Yeo', 'Victor Wong', 'Natalie Lim', 'Raymond Lee', 'Carmen Ong',
 'Howard Ng', 'Valerie Teo', 'Derrick Tan', 'Priscilla Lau', 'Louis Chen', 'Angela Yeo', 'Dennis Ho', 'Caroline Lim',
 'Ray Ng', 'Vivian Wong', 'Joel Tan', 'Christine Goh', 'Eric Chua', 'Lydia Teo', 'Colin Lau', 'Rebecca Tan',
 'Stanley Lee', 'Jasmine Ho', 'Harold Wong', 'Elaine Lim', 'Bryan Chen', 'Cecilia Ng', 'Philip Teo', 'Ivy Lau',
 'Leonard Tan', 'Joanna Ong', 'Vincent Chua', 'Angela Koh', 'Frank Wong', 'Theresa Lee', 'Oscar Ng', 'Naomi Tan',
 'Peter Chen', 'Claudia Ho', 'Victor Lau', 'Stephanie Lim', 'Lawrence Teo', 'Natalie Wong', 'Jeffrey Tan', 'Sandra Chua',
 'Aaron Lee', 'Rachel Ng', 'Gavin Ong', 'Eileen Ho', 'Simon Wong', 'Iris Teo', 'Marcus Tan', 'Amanda Lim',
 'Steven Chua', 'Phoebe Lau', 'Desmond Ng', 'Daphne Tan', 'Julian Wong', 'Cynthia Lee', 'Terrence Ho', 'Belinda Ong',
 'Wayne Chen', 'Candice Yeo', 'Lionel Lim', 'Doris Wong', 'Kelvin Chua', 'Gloria Ho', 'Herman Tan', 'Shirley Lee',
 'Clifford Teo', 'Hazel Ng', 'Gordon Wong', 'Sophie Tan', 'Douglas Chua', 'Esther Lim', 'Malcolm Lau', 'Joey Ng',
 'Kenneth Wong', 'Grace Tan', 'Terrence Lee', 'Mandy Ho', 'Roy Chen', 'Elsa Chua', 'Martin Ng', 'Ivy Yeo',
 'Francis Lim', 'Katrina Wong', 'Dominic Teo', 'Serene Tan', 'Henry Chua', 'Cheryl Lee', 'Anthony Wong', 'Diana Ho',
 'Nigel Tan', 'Jacqueline Ng', 'Clinton Teo', 'Pauline Lau', 'Alvin Wong', 'Sherilyn Tan', 'Joseph Lee', 'Catherine Yeo',
 'Luke Ng', 'Tracy Ho', 'Bernard Wong', 'Stella Tan', 'Harvey Lau', 'Michelle Chua', 'Chris Ng', 'Nora Lee',
 'Edwin Wong', 'Patricia Lim', 'Alex Tan', 'Renee Ong', 'Victor Chen', 'Elaine Yeo', 'Bryan Ng', 'Janet Ho',
 'Colton Wong', 'Tiffany Lau', 'Shawn Tan', 'Andrea Chua', 'Eugene Lee', 'Veronica Ng', 'Glenn Wong', 'Charlotte Tan',
 'Leon Ng', 'Madeline Ho', 'Trevor Chua', 'Joanne Wong', 'Clive Lee', 'Selena Tan', 'Howard Lim', 'Phoebe Ng',
 'Damian Wong', 'Kimberly Yeo', 'Marcus Ong', 'Elaine Tan', 'Noel Chua', 'Jessica Lee', 'Warren Wong', 'Susan Ho',
 'Keith Ng', 'Theresa Lau', 'Russell Tan', 'Melissa Chua'
]
invoice_types = ['recurring', 'opportunity']
statuses = ['pending', 'processing', 'success', 'fail', 'overdue']

def generate_mock_invoices():
    for i in range(1, 15):
        # Generate random dates
        created_date = datetime.now() 
        updated_date = created_date 
        
        invoice = {
            'invoice_id': f'IV-{i:03d}',
            'amount': Decimal(str(random.randint(1000, 100000))),
            'created_at': created_date.isoformat(),
            'customer_name': random.choice(customers),
            'invoice_type': random.choice(invoice_types),
            'status': random.choice(statuses),
            'updated_at': updated_date.isoformat()
        }
        
        table.put_item(Item=invoice)
        print(f"Created invoice: {invoice['invoice_id']}")

if __name__ == "__main__":
    generate_mock_invoices()
    print("Generated 15 mock invoices successfully!")
