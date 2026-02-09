from parsers.bbl_parser import BBLParser
from parsers.ttb_parser import TTBParser
from .kbank_parser import KBankParser
from .scb_parser import SCBParser

class ParserFactory:
    @staticmethod
    def get_parser(bank_name):
        parsers = {
            'scb_bank': SCBParser(),
            'kbank': KBankParser(),
            'bbl_bank': BBLParser(),
            'krungthai_bank': KBankParser(),
            'ttb_bank': TTBParser(),
        }
        return parsers.get(bank_name)