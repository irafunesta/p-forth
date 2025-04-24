import csv
import json
import sys, getopt
import datetime
import time
import re
from pathlib import Path

debug = False
 #fix this

def add(stack):
    if len(stack) > 1:
        num1 = stack.pop() 
        num2 = stack.pop()
        if num1 == None or num2 == None:
            print("None")
        stack.append(num1 + num2)
        return 0
    print("error not enough elements")
    return -1

def emit(stack):
    if len(stack) > 0:
        num1 = stack.pop() 
        print(num1)
        return 0
    print(stack)
    return 0

def print_stack(stack):
    print(stack)

words_dictionary = { "+":add, ".":emit, ".s":print_stack}

def execute_word(stack, word):
    # print("execute word:", word)
    try:
        number = int(word)
        stack.append(number)
    except ValueError:
        code = words_dictionary.get(word)
        if code == None:
            print(word , " ?")
            return -1
        
        return code(stack)
    return 0

def get_next_word(words, index):
    # print("words:", words)
    # print("index:", index)
    if index > len(words) - 1:
        return None
    return words[index]

def interpreter(filename, outputfile, table_name, split, separator) :
    
    now = datetime.datetime.now()
    format_date = now.strftime('%Y-%m-%d_%H-%M-%S')

    # output_path = Path(outputfile)

    # outputName = f'{outputfile}'
    # in_file = open(filename, 'r')

    integer_stack = []
    
    current_program = [] # for now i use words
    

    end = False
    while not end:
        input_code = input(">> ")
        word_pointer = 0
        if input_code == "q":
            end = True
            continue

        
        words = input_code.strip().split(" ")
        print(words)

        #execution one word at a time
        # word = words[word_pointer]
        # print("word:", word)
        run = True
        text_result = "ok"
        while run:
            # print("start loop")
            #in case checks for jumps
            word = get_next_word(words, word_pointer)
            # print("word:", word)
            if word != None:
                error = execute_word(integer_stack, word)
                # print("execution :",integer_stack)
                if error == -1 :
                    run = False
                    text_result = ""
                else:
                    word_pointer += 1
            else:
                run = False
                text_result = "Ok"
        
        print(text_result)
           
        
    print(f'END ------------------------ ')

# 10 do 1 . loop ||| if x = 1 then 3 else 6 ||| 1 1 cmp 3 else 6
# : cmp (n n -- ) (seek for the else, save the index, subtract 2 values, if res is 0, jump to the saved index)
# need to seek the next word, or the end of the jump 


def main(argv):
    inputfile = ''
    outputfile = ''
    table_name = ''
    split = False
    separator = ';'

    try:
        opts, args = getopt.getopt(argv,"hi:o:t:s:p:",["ifile=","ofile=", "table=", "split=", "sep="])
    except getopt.GetoptError:
        print ('test.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-t", "--table"):
            table_name = arg
        elif opt in ("-s", "--split"):
            try:
                print("split:", arg)
                split = int(arg)
            except ValueError:
                print("ERR value not a number")
                split = -1
        elif opt in ("-p", "--sep"):
            separator = arg
    
    # print ('Input file is ', inputfile)
    # print ('Output file is ', outputfile)
    # print ('table_name is ', table_name)
    # print ('split is ', split)
    # print ('separetor is ', separator)

    # start = time.perf_counter()

    interpreter(inputfile, outputfile, table_name, split, separator)

    # end = time.perf_counter()
    # elapsed = end - start
    # print(f'Time taken: {elapsed:.6f} seconds')

if __name__ == "__main__":
   main(sys.argv[1:])