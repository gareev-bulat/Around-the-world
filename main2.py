import sqlite3
import random


def add():
    global cursor
    new_word = input("word: ")
    translate = input("перевод: ")
    data = (new_word, 0, translate)
    cursor.execute("INSERT INTO words (name, iterator, translation) VALUES (?, ?, ?)", data)
    con.commit()

con = sqlite3.connect("words.db")

cursor = con.cursor()

while True:
    vod = input()
    if vod == '+':
        add()
    elif vod == 'тест':
        cursor.execute("SELECT * FROM words")
        all_data = cursor.fetchall()
        random.shuffle(all_data)
        for item in all_data:
            print(item[2])
            correct_answer = item[0]
            answer = input()
            if (answer == correct_answer):
                print("correct")
            else:
                print("incorrect", "-", "correct_answer:", correct_answer)












