import boto3
from datetime import datetime
from decimal import Decimal
import uuid

class Invoice:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-5')
        self.table = self.dynamodb.Table('hackathon-invoice')

    def create_invoice(self, invoice_id, customer_name, amount, invoice_type, status='pending'):
        item = {
            'invoice_id': invoice_id,
            'customer_name': customer_name,
            'amount': Decimal(str(amount)),
            'status': status,
            'invoice_type': invoice_type,
            'risk_level': 'low',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        self.table.put_item(Item=item)
        return invoice_id
    
    def update_invoice(self, invoice_id, **kwargs):
        update_expr = 'SET '
        expr_values = {}
        expr_names = {}
        
        for i, (key, value) in enumerate(kwargs.items()):
            placeholder = f'#key{i}'
            value_placeholder = f':value{i}'
            update_expr += f'{placeholder} = {value_placeholder}, '
            expr_values[value_placeholder] = value if not isinstance(value, float) else Decimal(str(value))
            expr_names[placeholder] = key
        
        update_expr += 'updated_at = :updated_at'
        expr_values[':updated_at'] = datetime.now().isoformat()
        
        self.table.update_item(
            Key={'invoice_id': invoice_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )
        

    def update_invoice_status(self, invoice_id, status):
        update_expr = 'SET #status = :status, updated_at = :updated_at'
        expr_values = {
            ':status': status,
            ':updated_at': datetime.now().isoformat()
        }
        
        self.table.update_item(
            Key={'invoice_id': invoice_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames={'#status': 'status'}
        )

    def get_invoice(self, invoice_id):
        response = self.table.get_item(Key={'invoice_id': invoice_id})
        return response.get('Item')

    def get_invoices_by_customer(self, customer_name):
        response = self.table.scan(
            FilterExpression='customer_name = :customer_name',
            ExpressionAttributeValues={':customer_name': customer_name}
        )
        return response.get('Items', [])
