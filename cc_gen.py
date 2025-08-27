import random, pytz, datetime, re

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def is_luhn_valid(card_number) -> bool:
    return luhn_checksum(card_number) == 0

def cc_gen(cc, mes='xx', ano='xxxx', cvv='rnd'):
    ccs = []
    while len(ccs) < 10:
        card = str(cc)
        digits = '0123456789'
        list_digits = list(digits)
        random.shuffle(list_digits)
        string_digits = ''.join(list_digits)
        card = card + string_digits
        new_list = list(card)
        list_emty = []

        for i in new_list:
            if i =='x':
                list_emty.append(str(random.randint(0,9)))
            else:
                list_emty.append(i)

        list_empty_string = ''.join(list_emty)
        card = list_empty_string

        if card[0] == '3':
            card = card[0:15]
        else:
            card = card[0:16]

        if mes == 'xx' or mes == 'rnd':
            mes_gen = random.randint(1, 12)
            if len(str(mes_gen)) == 1:
                mes_gen = '0' + str(mes_gen)
        else:
            if int(mes) > 12:
                return False
            else:
                mes_gen = mes

        if ano == 'rnd' or ano == 'xxxx':
            ano_gen = random.randint(2023,2040)
        else:
            ano_gen = ano
            if len(str(ano_gen)) == 2:
                ano_gen = '20' + str(ano_gen)

        if cvv == 'rnd' or cvv == 'xxx' or cvv == 'xxxx':
            if card[0:1] == '3':
                cvv_gen = random.randint(1000,9999)
            else:
                cvv_gen = random.randint(100,999)
        else:
            cvv = re.findall(r"[0-9]+", cvv)[0]

            if card[0:1] == '4':
                if len(cvv) < 3:
                    cvv_gen = str(cvv + str(random.randint(100,999)))[0:3]
                else:
                    cvv_gen = cvv
            elif card[0:1] == '5':
                if len(cvv) < 3:
                    cvv_gen = str(cvv + str(random.randint(100,999)))[0:3]
                else:
                    cvv_gen = cvv

            elif card[0:1] == '6':
                if len(cvv) < 3:
                    cvv_gen = str(cvv + str(random.randint(100,999)))[0:3]
                else:
                    cvv_gen = cvv
                
            elif card[0:1] == '3':
                if len(cvv) < 4:
                    cvv_gen = str(cvv + str(random.randint(1000,9999)))[0:4]
                else:
                    cvv_gen = cvv
            else:
                cvv_gen = cvv

        a = is_luhn_valid(card)
        if a:

            IST = pytz.timezone('US/Central') 
            now = datetime.datetime.now(IST)
            max_reintentos = 10
            intentos = 0

            while intentos < max_reintentos:
                intentos += 1

                if ((datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") <= datetime.datetime.strptime(f'{mes_gen}-{ano_gen}', "%m-%Y"))) == True :
                    x = str(card) + '|' + str(mes_gen) + '|' + str(ano_gen) + '|' + str(cvv_gen) + '\n'
                    added = ccs.append(x)
                    break
                    
                else:
                    intentos += 1
                    break
        
            else:
                continue
                
        else:
            continue

    return ccs