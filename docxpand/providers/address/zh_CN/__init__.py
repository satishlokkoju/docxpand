from collections import OrderedDict
import typing as tp
from chinese_address_generator import generator as address_generator
from faker.providers.address.zh_CN import Provider as AddressProvider


class Provider(AddressProvider):
    __use_weighting__ = True

    address_full_formats = OrderedDict(
        (
            ("{{address_line_1}}\n{{address_line_3}}", 0.6),
            ("{{address_line_1}}\n{{address_line_2}}\n{{address_line_3}}", 0.4),
        )
    )

    address_line_3_formats = OrderedDict(
        (
            ("园#幢###室", 0.1),
            ("村#组###号", 0.1),
            ("二街##号", 0.1),
            ("寓###", 0.1),
            ("村##号附#号", 0.1),
            ("村###号", 0.1),
            ("南路#号###室", 0.1),
            ("苑#幢#单元###室", 0.1),
            ("一里##号###室", 0.1),
            ("路##号#-#-#", 0.1)
        )
    )

    def address_line_1(self) -> str:
        # Lvl 3: province + city + county
        address = address_generator.generatelevel3().split()[0]
        return address

    def address_line_2(self) -> str:
        # Lvl 1: province + city
        address = address_generator.generatelevel2().split()[0]
        return address

    def address_line_3(self) -> str:
        if self not in self.generator.providers:
            self.generator.add_provider(self)
        pattern: str = self.random_element(self.address_line_3_formats)
        return self.numerify(self.generator.parse(pattern))
    
    def address(self) -> str:
        if self not in self.generator.providers:
            self.generator.add_provider(self)
        pattern: str = self.random_element(self.address_full_formats)
        return self.generator.parse(pattern)
