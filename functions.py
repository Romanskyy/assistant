import pickle
from prettytable import PrettyTable
from termcolor2 import colored
from classes import AddressBook, Record, Phone, Birthday
import nltk
import re
import pymorphy2
import itertools
import textwrap
from datetime import datetime


len_str = 105+19


def pretty_print(text, color='green'):

    if isinstance(text, str):
        text = [el.ljust(len_str) for el in text.split('\n')]
        text = '\n'.join(text)
        print(colored(text, color='green', attrs=['bold']))
        print(colored('৹' * len_str, color='green'))
    elif isinstance(text, (Record, AddressBook)):
        pretty_table(text, color='yellow', attrs=['reverse'])
    else:
        print(colored(str(text), color='red', attrs=['bold', 'blink']))


def pretty_input(text):

    print(colored(text, color='blue'))
    user_input = input('>>> ')
    print(colored('৹' * len_str, color='green'))
    return user_input


def pretty_table(addressbook, N=10, color='yellow'):
    # выводит на экран всю адресную книгу блоками по N записей. Основная обработка
    # реализована как метод класса addressbook, что позволяет использовать аналогичный
    # вывод для результатов поиска по запросам, так как функции поиска возвращают
    # объект типа addressbook с результатами
    n = int(N)
    if isinstance(addressbook, AddressBook):
        pretty_print(f'всего к выводу {len(addressbook)} записей: ')
        for block in addressbook.out_iterator(n):
            print(pretty(block))
            if len(block) == n:
                usr_choice = input(colored(
                    'Нажмите "Enter", или введите "q", что бы закончить просмотр.\n', 'yellow'))
                if usr_choice:
                    """Если пользователь вводит любой символ, его перебрасывает на основное меню."""
                    break
            continue
        return colored('Вывод окончен!', color)

    if isinstance(addressbook, Record):
        record = addressbook
        x = AddressBook()
        x[record.name] = record
        print(pretty(x))
    #print('объект не является ни записью ни адресной книгой')


def pretty(block):
    '''
        Данная функция создана исключительно для обработки функции show_all,
        1. Принимает блок
        2. Парсит его
        3. Добавляет обработанную инфу в таблицу
        4. Возвращает таблицу
        '''
    # from prettytable import ORGMODE
    # vertical_char=chr(9553), horizontal_char=chr(9552), junction_char=chr(9580)
    # vertical_char=chr(9475), horizontal_char=chr(9473), junction_char=chr(9547)
    #  vertical_char="⁝", horizontal_char="᠃", junction_char="྿"
    # ஃ ৹ ∘"܀" "܅" ྿ ፠ ᎒ ። ᠃
    if isinstance(block, Record):
        record = block
        block = AddressBook()
        block[record.name] = record
    table = PrettyTable([], vertical_char="ஃ",
                        horizontal_char="৹", junction_char="ஃ")
    titles = ('имя'.center(20), 'дата рождения'.center(15), 'телефоны'.center(
        15), 'email'.center(20), 'адрес'.center(20), 'заметки'.center(15))
    table.field_names = titles
    table.align['имя'.center(15)] = 'l'
    table.align['заметки'.center(15)] = 'l'

    for name, record in block.items():
        name = name.split()

        bd = [str(record.birthday)]

        phone = [phone.phone for phone in record.phones]
        w_em = textwrap.TextWrapper(width=20, break_long_words=True)
        email = w_em.wrap('\n'.join([email.email for email in record.emails]))

        w_ad = textwrap.TextWrapper(width=20, break_long_words=True)
        address = w_ad.wrap(record.address or '')

        w_no = textwrap.TextWrapper(width=15, break_long_words=True)
        note = ' \n'.join([f"{str(k)} : {v}" for k, v in record.note.items()])
        note = w_no.wrap(note or '')

        x = list(itertools.zip_longest(
            name, bd, phone, email, address, note, fillvalue=""))
        # print(x)
        for lst in x:
            table.add_row(lst)
    return colored(table, 'yellow')


def deserialize_users(path):
    """using the path "path" reads the file with contacts"""

    with open(path, "rb") as fh:
        addressbook = pickle.load(fh)

    return addressbook


def serialize_users(addressbook, path):
    """saves a file with contacts on the path (object pathlib.Path) to disk"""

    with open(path, "wb") as fh:
        pickle.dump(addressbook, fh)


def error_handler(func):
    # сюда вынесена обработка всех возникающих ошибок в ходе работы программы - как типов и
    # форматов, так и логические (дата рождения в будущем, попытка удалить несуществующий параметр и т.д.)
    def inner(*args):
        try:
            result = func(*args)
            return result
        except Exception as message:
            return message.args[0]

    return inner


def parse(input_string):  # --> ('key word', parameter)
    # извлекает команду и параметры из строки, возвращает в виде списка с
    # одним элементом - кортеж из двух элементов: команды и параметры

    def parse_phone(src):
        # функция принимает строку в качестве аргумента и ищет в ней номер телефона (справа)
        # Возвращает кортеж из двух аргументов - все, вплоть до номера телефона (без
        # пробелов слева и справа) и номера телефона. Если номер телефона не найден,
        # вместо него возвращается пустая строка.

        import re
        phone_regex = re.compile(r'[+]?[\d\-\(\)]{5,18}\s?$')
        match = phone_regex.search(src)
        if match is None:
            result = (src.strip(), '')
        else:
            result = (src[:match.start()].strip(), match.group())
        return result

    def parse_word(word):
        # фабричная функция. Производит функции синтаксического анализатора для
        # отдельных команд. Возвращает кортеж из команды, строку после команды
        # и номер телефона. Если номер телефона отсутствует, вместо него
        # возвращается пустая строка.

        l = len(word)

        def result(src):
            if src.casefold().startswith(word.casefold()):
                return word, *parse_phone(src[l:].lstrip())

        return result

    parse_scoup = [
        parse_word('hello'),
        parse_word('add'),
        # parse_word('change'),
        parse_word('phone'),
        parse_word('show all'),
        parse_word('exit'),
        parse_word('close'),
        parse_word('good bye'),
        parse_word('.'),
        parse_word('help'),
        parse_word('search'),
        parse_word('other phone'),
        parse_word('bd add')
    ]
    res_pars = [i(input_string) for i in parse_scoup if i(
        input_string)] or [('unrecognize', '', '')]

    return res_pars[0]


@error_handler
def get_handler(res_pars, addressbook):
    # получив результаты работы парсера функция управляет передачей параметров
    # и вызовм соотвествующего обработчика команды

    def help_f(*args):
        return '''формат команд:
        - add - формат: add name phone_number - добавляет новый контакт
        - other phone - формат: other phone name phone_number - добавляет дополнительный телефон в существующую запись
        - show all - формат: show all [N] - показывает всю адресную книгу. N - необязательный параметр - количество одновременно выводимых записей
        - exit/./close/goog bye - формат: exit - остановка работы с программой. Важно! чтобы сохранить все изменения и введенные данные - используйте эту команду
        - phone - формат: phone name - поиск телефона по имени. Можно ввести неполной имя либо его часть - программа выведет все совпадения
        - hello - формат: hello - просто Ваше привествие программе. Доброе слово - оно и для кода приятно)
        - bd add - формат: bd add name dd-mm-YYYY - ввод либо перезапись ранее введенной даты рождения. Соблюдайте формат ввода даты.
        - search - формат: search pattern - поиск совпадений по полям имени и телефонов. Будут выведены все записи в которых есть совпадения'''

    def hello_f(*args):
        return 'Привет! Чем я могу Вам помочь?'

    def exit_f(*args):
        return None

    def is_in(addressbook, name):
        return name in addressbook

    def enter_new_correct_name(addressbook):
        name = pretty_input('Введите новое имя ')
        while is_in(addressbook, name) or not name:
            if not name:
                name = pretty_input(
                    'У человека должно быть имя. Введите имя. Передумали ? Enter -выход в предыдущее меню')
            else:
                name = pretty_input(
                    'Введите другое имя. Такое имя уже есть (Enter -выход в предыдущее меню')
            if not name:
                return False
        return name

    def add_f(addressbook):
        #  сначала создает запись с именем
        #  потом последовательно вызывает функции
        # для заполнения телефона, д/р, заметки, и т.д.
        name = enter_new_correct_name(addressbook)
        if not name:
            return True  # если имя передумали вводить выходим в меню
        record = Record(name)
        addressbook.add_record(record)
        add_phone(record)
        change_bd(record)
        change_adr(record)
        add_eml(record)
        add_note(record)
        return f'в адресную книгу внесена запись: \n{pretty(record)}'

    def search_record(adressbook):
        pattern = pretty_input(
            'введите имя записи или часть имени/значения поля, которое однозначно определяет запись: ')
        res = addressbook.search(pattern)
        while len(res) != 1:
            pretty_print(f'найдено {len(res)} записей')
            print(f'{pretty(res)}')
            pattern = pretty_input(
                'введите более точный запрос или порядковый номер абонента в этой таблице (1/2/...) ')
            try:
                number_choice = int(pattern) - 1
                choice_name = list(res)[number_choice]
                one_record = addressbook[choice_name]
                res = AddressBook()
                res[one_record.name] = one_record

            except:
                res = addressbook.search(pattern)

        name, record = list(res.items())[0]
        pretty_print(f'найдена запись с именем {name}')
        return record

    @error_handler
    def change_name(record):
        if isinstance(record, Record):
            name = enter_new_correct_name(addressbook)
            # если имя передумали вводить  то прерываемся, ничего не делаем , выходим в меню
            if not name:
                return True
            addressbook.del_record(record.name)
            record.change_name(name)
            addressbook.add_record(record)
            return f'в записи изменено имя: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    @error_handler
    def add_note(record):
        if isinstance(record, Record):
            note_new = pretty_input(
                'введите заметку. Дата и время будут добавлены автоматически: ')
            record.add_note(note_new)
            return f'в запись добавлена заметка: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    @error_handler
    def add_eml(record):
        if isinstance(record, Record):
            email_new = pretty_input(
                'введите e-mail: ')
            record.add_email(email_new)
            return f'в запись добавлен e-mail: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соотвекстует более одной записи'

    def del_phone(record):
        pass

    @error_handler
    def change_eml(record):
        if isinstance(record, Record):
            answer = 'н'
            while answer != 'д':
                number_old_email = int(pretty_input(
                    'Какой email хотите поменять  ? введите его порядковый номер (1/2/3..) '))
                if 0 < number_old_email <= len(record.emails):
                    old_email = record.emails[number_old_email-1].email
                    answer = pretty_input(f'Этот номер {old_email}?(д/н)')
                else:
                    answer = 'н'
                    pretty_print('У абонента нет столько email')
            new_email = pretty_input('Введите новый email ')
            result = record.change_email(old_email, new_email)
            return f'У абонента изменен email: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    @error_handler
    def del_eml(record):
        if isinstance(record, Record):
            answer = 'н'
            while answer != 'д':
                number_old_email = int(pretty_input(
                    'Какой email хотите удалить  ? введите его порядковый номер (1/2/3..) '))
                if 0 < number_old_email <= len(record.emails):
                    old_email = record.emails[number_old_email-1].email
                    answer = pretty_input(f'Этот номер {old_email}?(д/н)')
                else:
                    answer = 'н'
                    pretty_print('У абонента нет столько email')
            result = record.del_email(old_email)
            return f'У абонента удален email: \ {pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    @error_handler
    def change_adr(record):
        if isinstance(record, Record):
            # address_old = record.address.__repr__() if record.address else 'пока не задан'
            # pretty_print(f'текущий адрес:  {address_old}')
            address_new = pretty_input('введите адрес ("ввод" - пропустить): ')
            record.add_address(address_new)
            return f'в запись добавлен адрес: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соотвекстует более одной записи'

    @error_handler
    def change_bd(record):
        if isinstance(record, Record):
            # birthday_old = record.birthday.__repr__() if record.birthday else 'пока не задан'
            # pretty_print(f'текущий день рождения:  {birthday_old}')
            birthday_str = pretty_input(
                'введите день рождения в формате дд-мм-гггг ("ввод" - пропустить): ')
            record.add_birthday(birthday_str)
            return f'в запись добавлен день рождения: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соотвекстует более одной записи'

    @error_handler
    def search_bd(addressbook):
        pretty_print(
            'Будем искать всех у кого дни рождения от первой введенной даты до второй введенной даты ')
        data_start = pretty_input('Первая дата (формат дд-мм-гггг) ')
        while True:
            try:

                datetime.strptime(data_start, "%d-%m-%Y")
                break
            except:
                pretty_print("Это не дата ")
                data_start = pretty_input(
                    'Еще раз. Первая дата (формат дд-мм-гггг) ')
        data_stop = pretty_input('Вторая дата (формат дд-мм-гггг)')
        try:
            datetime.strptime(data_stop, "%d-%m-%Y")
            result = addressbook.search_birthday(data_start, data_stop)
        except:
            pretty_print("Это не дата . Будем искать в одном дне")
            result = addressbook.search_birthday(data_start)
        return pretty_table(result, N=10)

    @error_handler
    def add_phone(record):
        if isinstance(record, Record):
            # позволяет добавить в запись дополнительный телефон
            phone = pretty_input('Введите номер телефона: ')
            record.add_phone(phone)
            return f'в запись добавлен новый телефон: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    @error_handler
    def change_phone(record):
        if isinstance(record, Record):
            answer = 'н'
            while answer != 'д':
                number_old_phone = int(pretty_input(
                    'Какой номер хотите поменять  ? введите его порядковый номер (1/2/3..) '))
                if 0 < number_old_phone <= len(record.phones):
                    old_phone = record.phones[number_old_phone-1].phone
                    answer = pretty_input(f'Этот номер {old_phone}?(д/н)')
                else:
                    answer = 'н'
                    pretty_print('У абонента нет столько номеров')
            new_phone = pretty_input('Введите новый номер ')
            result = record.change_phone(old_phone, new_phone)
            return f'в запись добавлен новый телефон: \n{pretty(record)}'
        return 'такой записи не существует или поисковом шаблону соответствует более одной записи'

    def change_f(addressbook):

        record = search_record(addressbook)
        pretty_table(record)
        pretty_print(menu_change)
        item_number = input('>>>  ')
        return func_change[item_number](record)

    def search(addressbook):
        user_input = pretty_input('Что Вы хотите найти? введите паттерн: ')
        # осуществляет поиск введенной строки во всех текстовых полях адресной книги
        result = addressbook.search(user_input)

        if not result:
            raise Exception('По данному запросу ничего не найдено')

        return pretty_table(result, N=10)

    def delete_f(addressbook):
        name = pretty_input('Введите имя ')
        result = addressbook.del_record(name)
        return result

    def show_all_f(addressbook, N=10):
        return pretty_table(addressbook, N)

    def unrecognize_f(res_pars, addressbook):
        print(f'вызвана функция unrecognize. Строка:  {res_pars}')
        COMMANDS = {'add': ['добавить', 'приплюсовать', 'нарастить', 'расширить', 'присовокупить', 'доложить', 'подбросить',
                    'прирастить', 'прибавить', 'приобщить', 'причислить', 'дополнить', 'додать', 'надбавить', 'увеличить', 'привнести',
                            'подбавить', 'присоединить', 'подбавить', 'внести', 'добавляй'],
                    'change': ['изменить', 'модифицировать', 'реконструировать', 'поменять', 'трансформировать', 'преобразовать',
                               'преобразить', 'переделать', 'видоизменить', 'обновить', 'переменить', 'сменить', 'изменить', 'менять', 'заменить'],
                    'remove': ['удалить', 'изьять', 'вытереть', 'выкинуть', 'вытереть', 'стререть', 'очистить', 'убрать', 'исключить',
                               'ликвидировать', 'удаляй', 'вытирай'],
                    'search': ['найти', 'выбрать', 'подобрать', 'показать', 'вывести', 'отобразить', 'искать', 'найди', 'ищи']}

        OBJECTS = {'record': ['имя', 'запись', 'человек', ],
                   'phone': ['телефон', 'номер'],
                   'birthday': ['день', 'дата', 'роды'],
                   'note': ['заметка', 'текст', 'тэг', 'примечание', 'описание', 'напоминание'],
                   'email': ['почта', 'мыло', 'email', 'e-mail', 'emails', 'e-mails', 'электронка'],
                   'adress': ['адрес', 'город', 'улица', 'ул.', 'проспект', 'поселок', 'село', 'деревня', 'бульвар', 'дом', 'квартира',
                              'кв.', 'площадь', 'пос.', 'набережная']}

        def pre_processing_str(raw_str):
            # Эта функция считает, что входящий текст - ОДНО предложение. \
            # осуществляет предварительную обработку строки - \
            # из предложения удаляет стоп-слова, \
            # предложение разбивает на слова и возвращает список слов без стоп-слов

            # получаем список слов
            text_words_list = (nltk.word_tokenize(raw_str))
            # читаем из библиотеки и дополняем список стоп-слов
            stop_words = nltk.corpus.stopwords.words('russian')
            stop_words.extend(['что', 'это', 'так', 'вот', 'быть',
                               'как', 'в', '—', '–', 'к', 'на', '...'])
            # удаляем из списка слов стоп-слова
            prepare_text_words_list = [
                i for i in text_words_list if (i not in stop_words)]
            return prepare_text_words_list

        def find_predictors(sentence, context_list, commands_scoup=COMMANDS, objects_scoup=OBJECTS):
            # получает на вход предварительно обработанный список слов из введенной строки, \
            # словарь возможных значений команд и словарь созможных значений объектов (то, над \
            # чем могут совершаться команды). Возвращает словарь, в котором ключами являются \
            # строки - соотвествующие предикторам, а значениями списки (для объектов которые могут \
            # имень несколько значений - телефоны, e-mail, команды или типы объектов), \
            # и одиночное значение (строка) для имени

            morph_ru = pymorphy2.MorphAnalyzer()

            def find_emails(sentence):
                regex = re.compile('[^ @]*@[^ ]*')
                result = regex.findall(sentence)
                return result if result else None

            def find_selected_text(sentence):
                # выделяет и возвращает из предложения текст, выделенный любой парой
                # (в начале и в конце) знаков ()
                # Если не найдено ничго, возвращает None
                regex = re.compile('[(].+[)]')
                result = regex.search(sentence)
                return result.group()[1:-1] if result else None

            def find_commands(word_of_morph_res, commands_scoup=COMMANDS):
                # из результатов морфлогического разбора отдельных слов выбираю ТОЛЬКО глаголы\
                # и сравниваю их нормальную форму с перечнем возможных команд. При совпадении\
                # возвращаю наименование команды как строку, иначе - None
                if word_of_morph_res.tag.POS == 'VERB' or word_of_morph_res.tag.POS == 'INFN':
                    for key, value in commands_scoup.items():
                        for word in value:
                            if word_of_morph_res.normal_form == word:
                                return key

            def find_objekts(word_of_morph_res, objects_scoup=OBJECTS):
                # из результатов морфлогического разбора отдельных слов выбираю ТОЛЬКО существительные\
                # и сравниваю их нормальную форму с перечнем возможных названий объектов. При совпадении\
                # возвращаю наименование объекта как строку, иначе - None
                res = None
                if word_of_morph_res.tag.POS == 'NOUN':
                    for key, value in objects_scoup.items():
                        res = key if [x for x in value if x ==
                                      word_of_morph_res.normal_form] else None
                        if res:
                            break
                return res

            def find_name(word_of_morph_res):
                # из результатов морфлогического разбора отдельных слов выбираю ТОЛЬКО с признаком,\
                # одушевленности и формирую из них одну строку. Если не найдено ничего - None
                res = []
                for word in word_of_morph_res:
                    # print(f'{word[0].normal_form}    {word[0].tag.animacy}')
                    if word.tag.animacy == 'anim':
                        res.append(word.normal_form)
                return ' '.join(res) if res else None

            def find_phones(sentence):
                regex = re.compile('\+?[0-9-xX()\[\]]{5,25}')
                result = regex.findall(sentence)
                return result if result else None

            predictors_dict = {
                'name': None,
                'selected_text': None,
                'commands': [],
                'objects': [],
                'phones': [],
                'emails': [],
                'context': None
            }
            predictors_dict['selected_text'] = find_selected_text(sentence)
            predictors_dict['phones'] = find_phones(sentence)
            predictors_dict['emails'] = find_emails(sentence)
            prepare_text_words_list = pre_processing_str(sentence)

            # проводим морфологический разбор слов в списке переданных подготовленных слов,\
            #  выбираем только наиболее вероятные знаяения для слов (выбор єлемента с индексом 0)
            morph_ru_result = [morph_ru.parse(word)[0]
                               for word in prepare_text_words_list]

            for word in morph_ru_result:
                command = find_commands(word, commands_scoup=COMMANDS)
                if command:
                    predictors_dict['commands'].append(command)

                object_for = find_objekts(word, objects_scoup=OBJECTS)
                if object_for:
                    predictors_dict['objects'].append(object_for)

            predictors_dict['name'] = find_name(morph_ru_result)

            if predictors_dict['name']:
                predictors_dict['context'] = predictors_dict['name']
            else:
                predictors_dict['context'] = None if len(
                    context_list) == 0 else context_list[-1]
            context_list.append(predictors_dict['context'])

            print(prepare_text_words_list)  # отладочный вывод

            print(predictors_dict)  # отладочный вывод
            if len(predictors_dict['commands']) > 1:
                raise Exception(
                    'Сложные команды разбивайте на предложения: не более одного действия в однм предложении (найти\заменить\добавить...)')
            return predictors_dict

        def handler_raw(predictors_dict, address_book):
            # получает на вход словарь с набором выявленных предикторов \
            # и на основе их анализа предлагает действия для их обработки
            # возвращает строку с рапортом о совершенных действиях или None\
            #  если никакие действия совершены быть не могут

            if ('search' in predictors_dict['commands']) and predictors_dict['selected_text']:
                chois = pretty_input(
                    f'''распознана команда ПОИСК. \n
                            текст в скобках, по всей видимости, является паттерном для поиска:\n
                            паттерн: {predictors_dict['selected_text']}\n
                            Выберите действие:
                                1. поиск по текущему паттерну
                                2. ввести новый паттерн
                                3. поиск по дням рождения (даты и интервалы дат)
                                4. выход
                        ''')
                if chois == '1':
                    return address_book.search(predictors_dict['selected_text'])
                elif chois == '2':
                    return search(address_book)
                elif chois == '3':
                    return search_bd(address_book)
                return True

            elif ('search' in predictors_dict['commands'] and not predictors_dict['selected_text']):
                print('точка 2')
                chois = pretty_input(
                    f'''
                        распознана команда ПОИСК. \n
                        подсказка: текст в круглых скобках в предложении с 
                        командой поиска будет воспринят как паттерн

                        в текущем вводе паттерн не распознан.
                        Выберите действие:
                            1. ввести паттерн для поиска
                            2. поиск по дням рождения (даты и интервалы дат)
                            3. выход
                    ''')
                if chois == '1':
                    return search(address_book)
                elif chois == '2':
                    return search_bd(address_book)
                return True

            if ('add' in predictors_dict['commands']) and (not predictors_dict['name']) and (not predictors_dict['objects']):
                chois = pretty_input(
                    f'''распознана команда ДОБАВИТЬ. \n
                            не распознано имя абонента
                            Выберите действие:
                                1. создать новую запись
                                4. выход
                        ''')
                if chois == '1':
                    return add_f(address_book)
                elif chois == '2':
                    return True
            elif ('add' in predictors_dict['commands']) and predictors_dict['name'] and (not predictors_dict['objects'] or ('record' in predictors_dict['objects'])) and not predictors_dict['phones'] and not predictors_dict['emails']:
                if is_in(address_book, predictors_dict['name']):
                    pretty_print(
                        f"запись с именем {predictors_dict['name']} существует")
                    item_number = pretty_input(menu_change)
                    record = address_book[predictors_dict['name']]
                    pretty_print(record)
                    return func_change[item_number](record)
                pretty_print(
                    f"запись с именем {predictors_dict['name']} не существует. Создаем запись:")
                record = Record(predictors_dict['name'])
                address_book.add_record(record)
                add_phone(record)
                change_bd(record)
                change_adr(record)
                add_eml(record)
                add_note(record)
                return f'в адресную книгу внесена запись: \n{record}'
            elif ('add' in predictors_dict['commands']) and (predictors_dict['name'] or predictors_dict['context']) and predictors_dict['objects'] and (predictors_dict['phones'] or predictors_dict['emails']):
                name = predictors_dict['name'] or predictors_dict['context']
                if is_in(address_book, name):
                    pretty_print(f"""в запись с именем {name} будет добавлены элементы:
                            телефон - {len(predictors_dict['phones'])} шт
                            e-mail  - {len(predictors_dict['emails'])} шт""")
                    choise = pretty_input("""подтвердите операцию:
                            1. продолжить
                            2. отменить""")
                    if choise == '1':
                        record = address_book[name]
                        for phone in predictors_dict['phones']:
                            record.add_phone(phone)
                        for email in predictors_dict['emails']:
                            record.add_email(email)
                        pretty_table(record)
                        return f"в запись {name} добавлено {len(predictors_dict['phones']) + len(predictors_dict['emails'])} элеметов"
                    return 'операция отменена'
                pretty_print(
                    f'записи с именем {name} - невозможно добавить что-либо. Сначала создайте запись.')
                pretty_print(
                    'При написании команд придерживайтесь правила - одно предложени описывает одно действие.')
                return 'обработка строки завершена'
            elif ('add' in predictors_dict['commands']) and (predictors_dict['name'] or predictors_dict['context']) and predictors_dict['selected_text'] and ('adress' in predictors_dict['objects'] or 'note' in predictors_dict['objects']):
                name = predictors_dict['name'] or predictors_dict['context']
                if is_in(address_book, name):
                    if 'adress' in predictors_dict['objects'] and 'note' in predictors_dict['objects']:
                        pretty_print(
                            f'нельзя за один шаг внести данные и в заметки и в адрес')
                        pretty_print(
                            'разделяйте действия по разным предложениям')
                        return 'обработка строки завершена'
                    elif 'adress' in predictors_dict['objects']:
                        pretty_print(
                            f"в запись {name} будет внесен адрес: \n   {predictors_dict['selected_text']}")
                        chois = pretty_input("""подтвердите действие:
                                1. продолжить
                                2. отменить""")
                        if chois == '1':
                            record = address_book[name]
                            record.add_address(
                                predictors_dict['selected_text'])
                            pretty_table(record)
                            return f"в запись {name} добавлен адрес"
                        return 'операция отменена'
                    elif 'note' in predictors_dict['objects']:
                        pretty_print(
                            f"в запись {name} будет внесена заметка: \n   {predictors_dict['selected_text']}")
                        chois = pretty_input("""подтвердите действие:
                                1. продолжить
                                2. отменить""")
                        if chois == '1':
                            record = address_book[name]
                            record.add_note(
                                predictors_dict['selected_text'])
                            pretty_table(record)
                            return f"в запись {name} добавлена заметка"
                        return 'операция отменена'
                pretty_print(
                    f'записи с именем {name} - невозможно добавить что-либо. Сначала создайте запись.')
                pretty_print(
                    'При написании команд придерживайтесь правила - одно предложени описывает одно действие.')
                return 'обработка строки завершена'
            elif ('add' in predictors_dict['commands']) and (predictors_dict['name'] or predictors_dict['context']) and ('birthday' in predictors_dict['objects']):
                name = predictors_dict['name'] or predictors_dict['context']
                if is_in(address_book, name):
                    record = address_book[name]
                    birthday_str = pretty_input(
                        'введите день рождения в формате дд-мм-гггг: ')
                    record.add_birthday(birthday_str)
                    pretty_table(record)
                    return f'в запись добавлен день рождения: \n {record.birthday.__repr__()}'
                pretty_print(
                    f'записи с именем {name} - невозможно добавить что-либо. Сначала создайте запись.')
                pretty_print(
                    'При написании команд придерживайтесь правила - одно предложени описывает одно действие.')
                return 'обработка строки завершена'

            if ('change' in predictors_dict['commands'] and not (predictors_dict['name'] or predictors_dict['context'])):
                pretty_print(
                    'изменение значений полей невозможно без указания имени записи\n имя записи не распознано')
                return 'обработка строки завершена'
            elif ('change' in predictors_dict['commands']):
                pass

        def gen_record(predictors_dict):
            # получает словарь выделенных из текста параметров и создает объект типа Record с этими параметрами
            record = Record(predictors_dict['name'])
            for elem in predictors_dict['phones']:
                record.add_phone(elem)
            # for elem in predictors_dict['emails']:
            #    record.add_email(elem)
            return record

            # из сырой строки создаем список предложений

        sentences_list = nltk.sent_tokenize(res_pars)
        context_list = []
        for sentence in sentences_list:
            predictors_dict = find_predictors(sentence, context_list)
            pretty_print(handler_raw(predictors_dict, addressbook))

        return 'обработка строки завершена'

    menu_change = '''
    Выберите необходимы пункт меню: 
                            0. Изменить имя
                            1. Добавить номер телефона (в записи может быть несколько разных номеров).
                            2. Изменить номер телефона.
                            3. Удалить номер телефона.
                            4. Добавить e-mail (в записи может быть несколько e-mail).
                            5. Изменить e-mail. 
                            6. Удалить e-mail.
                            7. Добавить/заменить дату рождения (может быть только одна).
                            8. Добавить/заменить почтовый адрес (может быть только один).
                            9. Добавить заметку (заметки не удаляются, они накапливаются).
                '''
    func_change = {'0': change_name,
                   '1': add_phone,
                   '2': change_phone,
                   '3': del_phone,
                   '4': add_eml,
                   '5': change_eml,
                   '6': del_eml,
                   '7': change_bd,
                   '8': change_adr,
                   '9': add_note,
                   }
    HANDLING = {
        '1': add_f,
        '2': change_f,
        '3': delete_f,
        '4': search,
        '5': search_bd,
        '6': show_all_f,
        '7': exit_f,
        'hello': hello_f,
        'exit': exit_f,
        '.': exit_f,
        'good bye': exit_f,
        'close': exit_f,
        'add': add_f,
        'show all': show_all_f,
        'phone': search,
        'search': search,
        'change': change_f,
        'unrecognize': unrecognize_f,
        'help': help_f,
        'other phone': add_phone,
        'bd add': change_bd
    }

    return HANDLING.get(res_pars)(addressbook) if HANDLING.get(res_pars) else unrecognize_f(res_pars, addressbook)
