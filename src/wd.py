import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from multiprocessing.pool import ThreadPool
import os
from pathlib import Path
import pickle
from random import shuffle
import sys
import requests
import getch
import signal
from bs4 import BeautifulSoup



HOME_PATH = str(Path.home())


def signal_handler(sig, frame):
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Data:
    def __init__(self):
        self.words = {}
        self.words_path = self._get_words_path()
        self.get_words()

    def _get_root_dir(self):
        root_dir = os.path.join(HOME_PATH, '.wd')
        is_exist = os.path.exists(root_dir)
        if not is_exist:
            os.makedirs(root_dir)
        return root_dir

    def _get_words_path(self):
        root_dir = self._get_root_dir()
        return os.path.join(root_dir, 'words')

    def save_words(self):
        with open(self.words_path, 'wb') as f:
            pickle.dump(self.words, f)

    def get_words(self):
        if os.path.isfile(self.words_path):
            with open(self.words_path, 'rb') as f:
                try:
                    self.words = pickle.load(f)
                except Exception:
                    pass
        return self.words
        
def load_dict():
    ecd = {}
    with open('./stardict.csv') as f:
        for w in csv.DictReader(f):
            ecd[w['word']] = w
    return ecd

data = Data()

def learn():

    def pick_batch():
        def random_pick(arr, num):
            shuffle(arr)
            return arr[:num], min(len(arr), num)

        def get_example_sentences(word, examples):
            page = requests.get(f"https://sentencedict.com/{word}.html")
            soup = BeautifulSoup(page.content, 'html.parser')
            try:
                children = soup.find(id='all').findChildren('div', recursive=False)
                examples[word] = list(map(lambda child: child.get_text(), filter(lambda child: child.get('id')==None, children)))
            except:
                examples[word] = ['404 not found']
        
        grep_0x = lambda arr: list(filter(lambda w: w['status']<2, arr))
        grep_1x = lambda arr: list(filter(lambda w: 10<=w['status']<=12, arr))

        all_words = list(data.words.values())
        words_1x, take_1x = random_pick(grep_1x(all_words), 2)
        for w in words_1x:
            w['status'] = 10
        words_0x, _ = random_pick(grep_0x(all_words), 10-take_1x)
        words = words_1x + words_0x
        examples = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            _ = [executor.submit(get_example_sentences, w['word'], examples) for w in words]
        return words, examples


    def learn_01(w, reveal):
        # word -> meaning
        # sys.stdout.flush()
        print(f'{"★" if w["star"] else "-"} {w["word"]} |{w["phonetic"]}| # {w["translation"]}' if reveal else f'{"★" if w["star"] else "-"} {w["word"]} |{w["phonetic"]}|'+' '*150, end='\r', flush=True)
        return 0


    def learn_12(w, _):
        # meaning -> word
        # sys.stdout.flush()
        print(f'{"★" if w["star"] else "-"} {w["translation"]}:', flush=True)
        ipt = input("spell: ")
        if ipt == w['word']:
            w['status'] += 10
            print('correct')
            return 1
        else:
            print(f'ans: {w["word"]}', end='\r')
            return 0

    learn = {
        0: learn_01,
        1: learn_12,
    }

    todo, examples = pick_batch()
    all_done = lambda arr: all(map(lambda w: (w['status']%10)>=2, arr))
    cur, n, reveal = 0, len(todo), False
    while not all_done(todo):
        stat = todo[cur]['status']%10
        word_str = todo[cur]['word']
        if stat == 2:
            cur = (cur+1)%n
            continue
        gain = learn[0 if reveal else stat](todo[cur], reveal)
        data.words[todo[cur]['word']]['status'] += gain
        data.save_words()

        ch = getch.getch()
        if ch == 'y':
            reveal = True
            data.words[word_str]['status'] += 1
            data.save_words()
        elif ch == 'n':
            reveal = True
        elif ch == ' ':
            reveal = False
            cur = (cur+1)%n
        elif ch == 's':
            data.words[word_str]['star'] = not data.words[word_str]['star']
            data.save_words()
        elif ch == 'e':
            sentences = examples[word_str] if word_str in examples else ['not found']
            ei, en, ml = 0, len(sentences), max([len(s) for s in sentences])
            while True:
                print(sentences[ei]+' '*(ml-len(sentences[ei])), end='\r')
                ch = getch.getch()
                if ch == 'j':
                    ei = (ei+1)%en
                elif ch == 'k':
                    ei = (ei-1)%en
                elif ch == ' ':
                    break

    print('10 words done ~~~ ！！！')

def import_words(file_path):
    ecd = load_dict()
    with open(file_path) as f:
        for word in f.readlines():
            word = word.strip()
            if word in ecd:
                data.words[word] = {
                    'word': word,
                    'phonetic': ecd[word]['phonetic'],
                    'definition': ecd[word]['definition'],
                    'translation': ecd[word]['translation'],
                    'status': 0,
                    'star': False
                }
    data.save_words()

def export_words(file_path):
    all_words = list(data.words.values())
    with open(file_path, 'w') as f:
        for w in filter(lambda w: w['star'], all_words):
            f.write(f'{w["word"]} # {w["phonetic"]} # {w["translation"]}\n')
        
    
def main():
    parser = argparse.ArgumentParser(
        description=(
            "words"
        )
    )
    parser.add_argument('-i', '--import', type=str, help='import words list')
    parser.add_argument('-e', '--export', type=str, help='export words list')

    args = vars(parser.parse_args())
    if args['import'] == None and args['export'] == None:
        learn()
    if args['import'] != None:
        import_words(args['import'])
    if args['export'] != None:
        export_words(args['export'])

if __name__ == '__main__':
    main()
