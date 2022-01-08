"""
wordle-trainer
"""
import os
import json
from enum import Enum
from random import choice
from copy import copy
from pathlib import Path
import typer


from wordle_trainer.wordle_dictionary import wordle_dictionary

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
ALPHA_ARRAY = list(ALPHABET)

_words_dictionary = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "words_dictionary.json")
)


class Hints(Enum):
    """
    Hints enum
    """

    EXCLUDE = "red"
    INCLUDE = "yellow"
    MATCH = "green"


class Hint:  # pylint: disable=too-few-public-methods
    """
    Hint class
    """

    def __init__(self, kind, position, letter):
        self.kind = kind
        self.position = position
        self.letter = letter

    def __repr__(self):
        return f'Hint({self.kind},{self.position},"{self.letter}")'


class Wordle:  # pylint: disable=too-many-instance-attributes
    """
    Wordle class
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        length=5,
        answer=None,
        turns=6,
        word_list=None,
        allowed_answers=None,
        show_hints=5,
        better_hints=False,
    ):
        self.length = length
        self.word_list = word_list
        if not self.word_list:
            raise Exception("word_list is empty")
        self.answer_list = allowed_answers if allowed_answers else self.word_list
        self.hint_list = self.answer_list if better_hints else self.word_list
        self.answer = (
            answer
            if answer
            else (
                choice(allowed_answers) if allowed_answers else choice(self.word_list)
            )
        )
        assert self.answer in self.word_list
        self.hints = []
        self.turns = turns
        self.alpha_array = copy(ALPHA_ARRAY)
        self.alphabet = copy(ALPHABET)
        self.hint_strings = []
        self.word_lists = []
        self.show_hints = show_hints

    def update_alphabet(self):
        """
        update_alphabet
        """
        if self.hints:
            for hint in sorted(
                self.hints, key=lambda h: 1 if h.kind == Hints.MATCH else 0
            ):
                index = ALPHA_ARRAY.index(hint.letter)
                self.alpha_array[index] = typer.style(
                    hint.letter, bg=hint.kind.value, fg="black"
                )
            self.alphabet = "".join(self.alpha_array)

    def print_board(self, print_hints=True):
        """
        print_board
        """
        typer.clear()
        typer.echo("W O R D L E")
        typer.echo()
        typer.echo(self.alphabet)
        typer.echo()
        for hint, length in zip(self.hint_strings, [len(x) for x in self.word_lists]):
            typer.echo(f"{hint}   {length} words remaining")
        if print_hints and self.show_hints > 0 and self.word_lists:
            typer.echo(
                f'Hints: {" ".join(self.word_lists[-1][0:min(self.show_hints,len(self.word_lists[-1]))])}{"..." if len(self.word_lists[-1]) > self.show_hints else ""}'  # pylint: disable=line-too-long
            )

    def hint_string(self, hints):
        """
        hint_string
        """
        arr = [""] * self.length
        for hint in hints:
            arr[hint.position] = typer.style(
                hint.letter, bg=hint.kind.value, fg="black"
            )
        return "".join(arr)

    def update_hints(self, hints):
        """
        update_hints
        """
        self.hints.extend(hints)
        self.word_lists.append(
            filter_word_list(
                self.word_lists[-1] if self.word_lists else self.hint_list,
                word_filter=lambda w: hints_filter(w, hints),
            )
        )
        self.hint_strings.append(self.hint_string(hints))

    def guess(self, word):
        """
        guess
        """
        hints = get_word_hints(self.answer, word)
        self.update_hints(hints)

    def reverse_guess(self, word, user_hint):
        """
        reverse_guess
        """
        hint_char_map = {"e": Hints.EXCLUDE, "i": Hints.INCLUDE, "m": Hints.MATCH}
        hints = [""] * self.length
        for i in range(self.length):
            hints[i] = Hint(hint_char_map[user_hint[i]], i, word[i])
        self.update_hints(hints)

    def play(self):
        """
        play
        """
        turn = 1
        done = False
        length_message = f"Please enter a {self.length}-letter word"
        extra_message = length_message
        while turn <= self.turns and not done:
            self.print_board()
            if extra_message:
                typer.echo(extra_message)
                extra_message = ""
            guess = typer.prompt(f"Guess {turn}/{self.turns}").lower()
            if len(guess) != self.length:
                extra_message = length_message
                continue
            if guess not in self.word_list:
                extra_message = "Please enter a valid word"
                continue
            self.guess(guess)

            self.update_alphabet()
            if guess == self.answer:
                done = True
                continue
            turn += 1

        self.print_board(print_hints=False)
        if done:
            typer.echo(f"Congratulations! {turn}/{self.turns}")
        else:
            typer.echo(f"Answer: {self.answer}")

    def reverse_play(self):
        """
        reverse_play
        """
        turn = 1
        done = False
        length_message = f"Please enter a {self.length}-letter word"
        extra_message = length_message
        while turn <= self.turns and not done:
            self.print_board()
            if extra_message:
                typer.echo(extra_message)
                extra_message = ""
            guess = typer.prompt(f"Guess {turn}/{self.turns}").lower()
            user_hint = typer.prompt(f"Hint {turn}/{self.turns}").lower()
            if len(guess) != self.length:
                extra_message = length_message
                continue
            if guess not in self.word_list:
                extra_message = "Please enter a valid word"
                continue
            if len(user_hint) != self.length:
                extra_message = length_message
                continue
            self.reverse_guess(guess, user_hint)
            extra_message = "Hints: " + " ".join(
                self.word_lists[-1][0 : min(self.show_hints, len(self.word_lists[-1]))]
            )

            if guess == self.answer:
                done = True
            turn += 1
            self.update_alphabet()

        self.print_board()


def get_word_hints(answer, guess):
    """
    get_word_hints
    """
    length = len(guess)
    if len(answer) != length:
        raise Exception(
            f"Guess and answer aren't the same length! ({length},{len(answer)})"
        )
    hints = []
    for i in range(length):
        if guess[i] == answer[i]:
            hints.append(Hint(Hints.MATCH, i, guess[i]))
        elif guess[i] in answer:
            hints.append(Hint(Hints.INCLUDE, i, guess[i]))
        else:
            hints.append(Hint(Hints.EXCLUDE, i, guess[i]))
    return hints


def is_valid_guess(word, hint=None):
    """
    is_valid_guess
    """
    if hint:
        if hint.kind == Hints.MATCH and (word[hint.position] != hint.letter):
            return False
        if hint.kind == Hints.EXCLUDE and (hint.letter in word):
            return False
        if hint.kind == Hints.INCLUDE and (
            (hint.letter not in word) or (word[hint.position] == hint.letter)
        ):
            return False
    return True


def hints_filter(word, hints):
    """
    hints_filter
    """
    for hint in hints:
        if not is_valid_guess(word, hint=hint):
            return False
    return True


def load_words_dict(fname):
    """
    load_words_dict
    """
    with open(fname, "r", encoding="utf-8") as file_obj:
        word_dict = json.load(file_obj)
    return [*word_dict]


def load_wordle_dict(fname):
    """
    load_wordle_dict
    """
    with open(fname, "r", encoding="utf-8") as file_obj:
        wordle_dict = json.load(file_obj)
    answers = wordle_dict["answers"]
    allowed = wordle_dict["answers"] + wordle_dict["allowed"]
    return allowed, answers


def filter_word_list(word_list, word_filter=None):
    """
    filter_word_list
    """
    if word_filter:
        return list(filter(word_filter, word_list))
    return word_list


app = typer.Typer()


@app.command()
def main(  # pylint: disable=too-many-arguments
    length: int = typer.Option(
        5,
        "--length",
        "-l",
        help="Length of word to guess. Only useful if used with --words-json .",
    ),
    turns: int = typer.Option(6, "--turns", "-t", help="Number of turns."),
    show_hints: int = typer.Option(
        5, "--show-hints", "-s", help="Number of hints to show."
    ),
    reverse: bool = typer.Option(
        False,
        "--reverse",
        hidden=True,
        help="Play with user provided clues. Useful for showing hints for other games.",
    ),
    better_hints: bool = typer.Option(
        False,
        "--better-hints",
        "-b",
        help="Limit the pool of hints to only the possible answers for the official wordle game.",
    ),
    words_json: Path = typer.Option(
        None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
        show_default=False,
        help="Json file of valid words.",
    ),
):
    """
    A Python Wordle clone for the terminal.
    """
    answers = None
    if words_json:
        word_list = filter_word_list(
            load_words_dict(words_json), word_filter=lambda w: len(w) == length
        )
    else:
        word_list, answers = (
            wordle_dictionary["allowed"] + wordle_dictionary["answers"],
            wordle_dictionary["answers"],
        )

    playing = True
    while playing:
        game = Wordle(
            length=length,
            turns=turns,
            word_list=word_list,
            allowed_answers=answers,
            show_hints=show_hints,
            better_hints=better_hints,
        )
        if reverse:
            game.reverse_play()
        else:
            game.play()

        playing = (
            typer.prompt("Play again? [y]/n", default="y", show_default=False)
            .lower()
            .startswith("y")
        )


if __name__ == "__main__":
    app()
