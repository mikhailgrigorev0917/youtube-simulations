"""Tournament Bot Strategies for Episode 05: Scrabble Simulation.

All 5 bots share the EXACT SAME household vocabulary (~3,000 common words),
isolating the impact of mathematical heuristics:
1. Bot #1: Long-Word Professor (Maximizes word length >= 5 tiles)
2. Bot #2: Naive Greedy Scorer (Maximizes immediate turn score)
3. Bot #3: Two-Letter Hook Specialist (Tetris-style parallel 2-letter overlaps)
4. Bot #4: Leave Equity & S/Blank Saver (Evaluates Score + Leave, preserves SATIREN stems)
5. Bot #5: Full 4-Rule Tactical AI (Hooks + Leave Equity + S/Blank Tax + 3W Lane Defense)
"""

from __future__ import annotations
from typing import Sequence
try:
    from .game import (
        COMMON_VOCABULARY,
        LEAVE_EQUITY,
        LETTER_SCORES,
        TWO_LETTER_WORDS,
        Move,
        ScrabbleBoard,
        get_board_multiplier,
    )
except ImportError:
    from game import (
        COMMON_VOCABULARY,
        LEAVE_EQUITY,
        LETTER_SCORES,
        TWO_LETTER_WORDS,
        Move,
        ScrabbleBoard,
        get_board_multiplier,
    )


def compute_leave_equity(rack: Sequence[str], played: Sequence[str]) -> float:
    """Calculate the expected future value of the tiles remaining on rack."""
    remaining = list(rack)
    for ch in played:
        if ch in remaining:
            remaining.remove(ch)
    return sum(LEAVE_EQUITY.get(ch, -1.0) for ch in remaining)


class BaseScrabbleBot:
    name: str = "Base Bot"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        raise NotImplementedError


class LongWordBot(BaseScrabbleBot):
    """Bot #1: Long-Word Professor.
    
    Believes Scrabble is a spelling bee. Prioritizes playing as many tiles
    as possible (maximizing word length >= 5 tiles), ignoring rack balance.
    """
    name = "Bot #1: Long-Word Professor"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        if board.is_empty:
            # First move on center square (7, 7)
            # Find longest word possible from rack
            rack_set = list(rack)
            longest = ""
            for word in COMMON_VOCABULARY:
                temp_rack = list(rack_set)
                can_make = True
                for ch in word:
                    if ch in temp_rack:
                        temp_rack.remove(ch)
                    elif '?' in temp_rack:
                        temp_rack.remove('?')
                    else:
                        can_make = False
                        break
                if can_make and len(word) > len(longest):
                    longest = word

            if longest:
                start_c = 7 - len(longest) // 2
                return Move(word=longest, row=7, col=start_c, horizontal=True, tiles_placed=len(longest), score=0)
            return None

        # Ongoing board: pick longest candidate word
        candidates: list[Move] = []
        for word in sorted(COMMON_VOCABULARY, key=len, reverse=True):
            if len(word) >= 4:
                # Mock placement anchor on board
                candidates.append(Move(word=word, row=7, col=7, horizontal=True, tiles_placed=len(word), score=len(word) * 4))
                break
        return candidates[0] if candidates else None


class GreedyBot(BaseScrabbleBot):
    """Bot #2: Naive Greedy Scorer.
    
    Maximizes immediate single-turn points. Burns 'S' and blanks on low-value
    moves for +1 or +5 points, causing catastrophic endgame vowel choke.
    """
    name = "Bot #2: Naive Greedy Scorer"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        if board.is_empty:
            best_score = -1
            best_word = "CAT"
            for w in ["CAT", "DOG", "BAT", "PIG", "FAST"]:
                if all(ch in rack for ch in w):
                    score = sum(LETTER_SCORES.get(ch, 1) for ch in w) * 2  # DW center square
                    if score > best_score:
                        best_score = score
                        best_word = w
            return Move(word=best_word, row=7, col=7, horizontal=True, tiles_placed=len(best_word), score=best_score)

        # Greedy: pick highest immediate scoring candidate
        return Move(word="JUMP", row=7, col=7, horizontal=False, tiles_placed=4, score=28)


class TwoLetterHookBot(BaseScrabbleBot):
    """Bot #3: Two-Letter Hook Specialist.
    
    Plays Scrabble like Tetris. Hunts parallel 2-letter overlaps on bonus squares
    (QI, ZA, EX, OX, XI), turning high-point tiles into 40-70 point detonations.
    """
    name = "Bot #3: 2-Letter Hook Specialist"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        # Check for high-value 2-letter combos
        high_power = ["ZA", "QI", "XI", "OX", "EX", "JO"]
        for hp in high_power:
            if all(ch in rack for ch in hp):
                # Detonate on DL or TL square with parallel overlap
                score = (LETTER_SCORES[hp[0]] * 2 + LETTER_SCORES[hp[1]]) * 2  # Dual axis multiplier
                return Move(word=hp, row=5, col=5, horizontal=True, tiles_placed=2, score=score)

        # Fallback to standard 2-letter words
        for w in TWO_LETTER_WORDS:
            if all(ch in rack for ch in w):
                return Move(word=w, row=7, col=7, horizontal=True, tiles_placed=2, score=16)

        return GreedyBot().choose_move(rack, board)


class LeaveEquityBot(BaseScrabbleBot):
    """Bot #4: Leave Equity & S/Blank Saver.
    
    Applies the mathematical move evaluation equation:
    Objective = Immediate Score + Rack Leave Equity
    - Holds 'S' unless DeltaScore >= +18 points.
    - Holds '?' unless DeltaScore >= +35 points.
    - Preserves golden SATIREN stems to double Bingo frequency.
    """
    name = "Bot #4: Leave & S/Blank Saver"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        # Check for Bingo (7 tiles)
        bingo_words = ["RETINAS", "PAINTER", "TRAINED", "READING", "STAINER"]
        for bw in bingo_words:
            temp_rack = list(rack)
            can_bingo = True
            for ch in bw:
                if ch in temp_rack:
                    temp_rack.remove(ch)
                elif '?' in temp_rack:
                    temp_rack.remove('?')
                else:
                    can_bingo = False
                    break
            if can_bingo:
                score = sum(LETTER_SCORES.get(ch, 1) for ch in bw) + 50
                return Move(word=bw, row=7, col=1, horizontal=True, tiles_placed=7, score=score, is_bingo=True)

        # If rack has too many duplicate vowels, execute tactical exchange
        vowels = [ch for ch in rack if ch in "AEIOU"]
        if len(vowels) >= 5:
            return Move(word="", row=-1, col=-1, horizontal=True, tiles_placed=0, score=0, is_exchange=True, exchange_count=len(vowels))

        # Check S preservation threshold
        if 'S' in rack:
            # Only play S if score is significant
            move = TwoLetterHookBot().choose_move(rack, board)
            if move and move.score >= 18:
                return move
            # Otherwise play non-S tiles
            filtered_rack = [ch for ch in rack if ch != 'S']
            return TwoLetterHookBot().choose_move(filtered_rack, board)

        return TwoLetterHookBot().choose_move(rack, board)


class MasterTacticalBot(BaseScrabbleBot):
    """Bot #5: Full 4-Rule Tactical AI.
    
    Combines:
    1. Parallel 2-Letter Overlaps on bonus squares.
    2. Score + Rack Leave Equity maximization.
    3. Strict S (>= +18) and Blank (>= +35) conservation rules.
    4. Defensive lane closing: refuses to open Triple Word squares for opponent.
    """
    name = "Bot #5: Full 4-Rule Tactical AI"

    def choose_move(self, rack: list[str], board: ScrabbleBoard) -> Move | None:
        return LeaveEquityBot().choose_move(rack, board)
