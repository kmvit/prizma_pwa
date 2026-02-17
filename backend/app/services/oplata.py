import decimal
import hashlib
from urllib.parse import urlencode
from loguru import logger


class RobokassaService:
    def __init__(self, merchant_login: str, merchant_password_1: str, merchant_password_2: str, is_test: int):
        self.merchant_login = merchant_login
        self.merchant_password_1 = merchant_password_1
        self.merchant_password_2 = merchant_password_2
        self.is_test = is_test

    def calculate_signature(self, *args) -> str:
        return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()

    def check_signature_success(self, out_sum, inv_id, received_signature):
        out_sum_str = "{:.2f}".format(float(out_sum)) if not isinstance(out_sum, str) else out_sum
        signature = self.calculate_signature(out_sum_str, inv_id, self.merchant_password_1)
        return signature.lower() == received_signature.lower()

    def check_signature_result(self, out_sum, inv_id, received_signature):
        out_sum_str = "{:.2f}".format(float(out_sum)) if not isinstance(out_sum, str) else out_sum
        signature = self.calculate_signature(out_sum_str, inv_id, self.merchant_password_2)
        return signature.lower() == received_signature.lower()

    def generate_payment_link(
        self,
        cost: decimal.Decimal,
        number: int,
        description: str,
        is_test: int,
        success_url: str = None,
        fail_url: str = None,
        robokassa_payment_url: str = 'https://auth.robokassa.ru/Merchant/Index.aspx',
    ) -> str:
        out_sum = "{:.2f}".format(float(cost))
        signature = self.calculate_signature(
            self.merchant_login, out_sum, number, self.merchant_password_1
        )
        data = {
            'MerchantLogin': self.merchant_login,
            'OutSum': out_sum,
            'InvId': number,
            'Description': description,
            'SignatureValue': signature,
            'IsTest': is_test
        }
        if success_url:
            data['SuccessURL'] = success_url
        if fail_url:
            data['FailURL'] = fail_url
        link = f'{robokassa_payment_url}?{urlencode(data)}'
        logger.debug(f"[Robokassa] MerchantLogin={self.merchant_login}, OutSum={out_sum}, InvId={number}, IsTest={is_test}, SuccessURL={success_url}")
        return link
