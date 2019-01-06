# Copyright (C) 2019 Yossi Gottlieb
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import struct

class Entry(object):
    def __init__(self, data):
        self.hdr = struct.unpack_from('BB', data, 0x0)
        if self.hdr != (0x94, 0x03):
            raise ValueError('Invalid entry')

        # Name length
        name_len = struct.unpack_from('B', data, 0x16c)[0]

        # Name
        start = 0x16e
        end = start + (name_len * 2)
        self.name = data[start:end].decode('utf-16')
        self.phone = self.__decode_phone(data)

    @staticmethod
    def __decode_digit(value):
        if value >= 0 and value <= 9:
            return str(value)
        if value == 10:
            return '*'
        if value == 15:
            return ''
        if value == 11:
            return '#'  # Just a guess
        raise ValueError('Unknown digit value {}'.format(value))

    def __decode_phone(self, data):
        phone_len, extra = struct.unpack_from('bb', data, 0x12a)
        phone = ''
        if extra & 0x10:
            phone += '+'
        for byte in data[0x12c:0x12c+phone_len]:
            phone += self.__decode_digit(byte & 0x0f)
            phone += self.__decode_digit(byte >> 4)
        return phone

    def vcard(self):
        return 'BEGIN:VCARD\nVERSION:3.0\nN:{name}\n' \
               'FN:{name}\nTEL;type=HOME:{phone}\n' \
               'END:VCARD\n'.format(name=self.name, phone=self.phone)

    def __str__(self):
        return '<Entry name={} phone={}>'.format(self.name, self.phone)

def process(infile, outfile):
    header = infile.read(0x244)
    entries = 0
    while True:
        data = infile.read(0x3ac)
        if not data:
            break
        entry = Entry(data)
        outfile.write(entry.vcard())
        entries += 1
    print('Exported {} entries.'.format(entries))

def main():
    parser = argparse.ArgumentParser(
        description='Nokia 3310 phonebook.ib exporter')
    parser.add_argument('infile', type=argparse.FileType('rb'),
                        help='Phonebook file to read')
    parser.add_argument('outfile', type=argparse.FileType('w', encoding='utf8'),
                        help='VCF File to write')
    args = parser.parse_args()
    process(args.infile, args.outfile)

if __name__ == '__main__':
    main()
