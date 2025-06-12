import random, string, os
import sys
import unicodedata
sys.set_int_max_str_digits(9999)

languages = {"geometry": [0x25A0, 0x25FF], 
            "khmer": [0x19E0, 0x19FF], 
            "olchiki": [0x1C50,0x1C7F],
            "english": [ord('a'), ord('z')],
            "runic": [0x16A0, 0x16FF],
            "chinese": [0x4E00, 0x9FFF],
            "chinese_small": [0x4E00, 0x4E00+100],
            "cuneiform": [0x12000, 0x123FF],
            "phaistos": [0x101D0,0x101FF], #not rendering
            "hieroglyph": [0x13000,0x1342F],
            "all": [0x0000, 0xD799],
            "ascii": [0x0020, 0x007F],
            "binary": [0x0030, 0x0031],
            "box": [0x2500, 0x257F]
            }

language = "binary"

# canonical sizes
max_page_content_length = 100
max_walls = 4
max_shelves = 5
max_volumes = 32
max_pages = 410


hexagon_base = 36
# TODO: can I get shorter addresses by making base larger than 36?

def searchByContent(text, language, max_length = 3200, library_coordinate = None,):
    if library_coordinate == None:
        wall = str(random.randint(1, max_walls))
        shelf = str(random.randint(1, max_shelves))
        volume = str(random.randint(1, max_volumes)).zfill(2)
        page = str(random.randint(1, max_pages)).zfill(3)
        library_coordinate = int(page + volume + shelf + wall)

    charset_start = languages[language][0]
    charset_end = languages[language][1] + 1
    charset_length = charset_end - charset_start
    if language != "all":
        text = ''.join([c for c in text if ord(c) <= charset_end and ord(c) >= charset_start])
    else:
        text = ''.join([c for c in text])
    additional_text = [chr(int(random.random() * charset_length) + charset_start) for _ in range(max_length - len(text))]
    text += "".join(additional_text)

    sum_value = 0
    for i, c in enumerate(text[::-1]):
        char_value = ord(c) - charset_start
        sum_value += char_value * (charset_length**i)

    result = library_coordinate * (charset_length**max_length) + sum_value
    result = convertToBase(result, hexagon_base)
    total_address = result + ':' + wall + ':' + shelf + ':' + volume + ':' + page
    return total_address

def searchByAddress(address, language, max_length=3200):
    charset_start = languages[language][0]
    charset_end = languages[language][1] + 1
    charset_length = charset_end - charset_start

    hexagon_address, wall, shelf, volume, page = address.split(':')
    volume = volume.zfill(2)
    page = page.zfill(3)
    library_coordinate = int(page + volume + shelf + wall)

    seed = int(hexagon_address, hexagon_base) - library_coordinate * (charset_length**max_length)
    hexagon_base_result = convertToBase(seed, hexagon_base)
    result = convertToBase(int(hexagon_base_result, hexagon_base), charset_length, language)

    if len(result) < max_length:
        random.seed(result)
        while len(result) < max_length:
            # result += charset[int(random.random() * len(charset))]
            result += chr(int(random.random() * charset_length) + charset_start)
    elif len(result) > max_length:
        result = result[-max_length:]
    return result

def convertToBase(x, base, language = None):
    if base == 36: digs = string.digits + 'abcdefghijklmnopqrstuvwxyz'
    elif base == 10: digs = '0123456789'
    elif base == 60: digs = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    else: 
        charset_start = languages[language][0]
        charset_end = languages[language][1] + 1
        charset_length = charset_end - charset_start
        digs = [chr(x) for x in range(charset_start, charset_end + 1)]

    if x < 0: sign = -1
    elif x == 0: return digs[0]
    else: sign = 1

    x *= sign
    
    chars = []
    while x:
        remainder = x % base
        chars.append(digs[remainder])
        x //= base
    if sign < 0:
        chars.append('-')
    chars.reverse()
    return ''.join(chars)


def get_full_page(search_term, language, max_length = 3200):
    address = searchByContent(search_term, language = language, max_length = max_length)
    full_page = searchByAddress(address, language=language, max_length = max_length)
    return full_page

def change_encoding(binary_encoding, text):
    if binary_encoding == True:
        content = []
        byte_array = bytearray(int(text[i:i+8], 2) for i in range(0, len(text), 8))
        for i in range(0, len(byte_array), 4):
            chunk = byte_array[i:i+4]
            try:
                character = chunk.decode('utf-32')
                if is_displayable(character):
                    content.append(character)
                else:
                    content.append('□')
            except:
                content.append('□')
        content = "".join(content)
    else:
        utf_string = text.encode('utf-32')
        content = ''.join(f'{byte:08b}' for byte in utf_string)
    return content

def is_displayable(character):
    # print out whitespace characters
    if character  in ('\t', '\n'):
        return True
    
    category = unicodedata.category(character)

    if (
        category.startswith('C') or 
        category.startswith('M') or 
        unicodedata.combining(character) or
        category in ('Co', 'Cs', 'Cn', 'Zl', 'Zp') or 
        not character.isprintable()
    ):
        return False
    # Exclude some known non-characters and zero-width
    if ord(character) in {0xFFFE, 0xFFFF, 0x200B, 0x200C, 0x200D, 0x2060}:
        return False
    return True