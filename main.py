import json
import random
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from questions import default_quizzes
from quiz import Quiz


STATE_PATH = Path(__file__).resolve().with_name("state.json")


def read_number(prompt, minimum, maximum, *, allow_hint=False):
    while True:
        raw = input(prompt).strip()
        if allow_hint and raw.lower() == "h":
            return "h"
        if not raw:
            print("입력이 비어 있습니다. 숫자를 입력하세요.")
            continue
        try:
            number = int(raw)
        except ValueError:
            print("정수를 입력하세요.")
            continue
        if minimum <= number <= maximum:
            return number
        print(f"{minimum}~{maximum} 사이의 번호를 입력하세요.")


def read_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("내용을 입력하세요.")


class QuizGame:
    def __init__(self):
        self.quizzes = default_quizzes()
        self.best_score = None
        self.history = []
        self.needs_save = False

    def show_menu(self):
        print("\n=== 볼트빈 커피 퀴즈 ===")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")
        print("6. 퀴즈 삭제")
        print("7. 점수 기록")

    def read_answer(self, quiz):
        prompt = "정답 번호 (H: 힌트): " if quiz.hint else "정답 번호: "
        used_hint = False
        while True:
            guess = read_number(prompt, 1, len(quiz.choices), allow_hint=bool(quiz.hint))
            if guess != "h":
                return guess, used_hint
            print(f"힌트: {quiz.hint}")
            print("힌트를 본 문제는 정답을 맞혀도 배점의 절반을 받습니다.")
            used_hint = True

    def play(self):
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return

        available = len(self.quizzes)
        total = read_number(f"풀 문제 수 (1~{available}): ", 1, available)
        selected = random.sample(self.quizzes, total)
        correct = 0
        half_points = 0
        print(f"\n총 {total}문제를 시작합니다.")
        for number, quiz in enumerate(selected, start=1):
            print(f"\n[문제 {number}/{total}]")
            quiz.show()
            guess, used_hint = self.read_answer(quiz)
            if quiz.is_correct(guess):
                correct += 1
                half_points += 1 if used_hint else 2
                print("정답입니다!")
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다. ({quiz.choices[quiz.answer - 1]})")

        score = half_points * 100 // (2 * total)
        print(f"\n결과: {total}문제 중 {correct}문제 정답 ({score}점)")
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            print(f"새 최고 점수입니다. ({score}점)")

        self.history.append({
            "played_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "question_count": total,
            "score": score,
        })
        self.needs_save = True
        self.save_state()

    def add_quiz(self):
        print("\n새 퀴즈를 등록합니다.")
        question = read_text("문제: ")
        choices = []
        for number in range(1, 5):
            choices.append(read_text(f"선택지 {number}: "))
        answer = read_number("정답 번호: ", 1, 4)
        hint = input("힌트 (없으면 Enter): ").strip()
        self.quizzes.append(Quiz(question, choices, answer, hint))
        self.needs_save = True
        if self.save_state():
            print("퀴즈를 추가하고 저장했습니다.")
        else:
            print("퀴즈를 추가했습니다. 종료하기 전까지 이 게임에서 사용할 수 있습니다.")

    def show_quizzes(self):
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return

        print(f"\n등록된 퀴즈 ({len(self.quizzes)}개)")
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"  {number}. {quiz.question}")

    def delete_quiz(self):
        self.show_quizzes()
        if not self.quizzes:
            return

        number = read_number("삭제할 문제 번호: ", 1, len(self.quizzes))
        print(f"삭제할 문제: {self.quizzes[number - 1].question}")
        confirm = read_number("1. 삭제  2. 취소: ", 1, 2)
        if confirm == 2:
            print("삭제를 취소했습니다.")
            return

        del self.quizzes[number - 1]
        self.needs_save = True
        if self.save_state():
            print("퀴즈를 삭제하고 저장했습니다.")
        else:
            print("이 게임에서 퀴즈를 삭제했습니다. 저장 파일에는 아직 반영되지 않았습니다.")

    def show_history(self):
        if not self.history:
            print("아직 저장된 게임 기록이 없습니다.")
            return

        print("\n점수 기록 (최근 순)")
        for record in reversed(self.history):
            played_at = record["played_at"].replace("T", " ", 1)
            print(f"  {played_at} | {record['question_count']}문제 | {record['score']}점")

    def show_best_score(self):
        if self.best_score is None:
            print("아직 퀴즈를 끝까지 푼 기록이 없습니다.")
        else:
            print(f"최고 점수: {self.best_score}점")

    def load_state(self):
        try:
            raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if not isinstance(raw["quizzes"], list):
                raise ValueError("퀴즈 목록 형식이 올바르지 않습니다.")
            default_hints = {
                (quiz.question, tuple(quiz.choices), quiz.answer): quiz.hint
                for quiz in default_quizzes()
            }
            quizzes = []
            for item in raw["quizzes"]:
                quiz = Quiz.from_dict(item)
                # Old saves lack a hint field. Only reuse hints for unchanged default questions.
                if "hint" not in item:
                    key = (quiz.question, tuple(quiz.choices), quiz.answer)
                    quiz.hint = default_hints.get(key)
                quizzes.append(quiz)
            best_score = raw["best_score"]
            if best_score is not None and (
                type(best_score) is not int or not 0 <= best_score <= 100
            ):
                raise ValueError("최고 점수는 0~100 사이의 정수여야 합니다.")
            history = raw.get("history", [])
            if not isinstance(history, list):
                raise ValueError("점수 기록 목록 형식이 올바르지 않습니다.")
            for record in history:
                datetime.fromisoformat(record["played_at"])
                count = record["question_count"]
                score = record["score"]
                if (
                    type(count) is not int or count < 1
                    or type(score) is not int or not 0 <= score <= 100
                ):
                    raise ValueError("점수 기록의 문제 수 또는 점수가 올바르지 않습니다.")
        except FileNotFoundError:
            return
        except (KeyError, TypeError, ValueError):
            print("저장 파일이 손상되어 기본 퀴즈로 복구합니다.")
            self.needs_save = True
        except OSError:
            print("저장 파일을 읽지 못해 기본 퀴즈로 시작합니다.")
        else:
            self.quizzes = quizzes
            self.best_score = best_score
            self.history = history
            print(f"저장한 퀴즈 {len(quizzes)}개와 점수 기록을 불러왔습니다.")

    def save_state(self):
        if not self.needs_save:
            return True

        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "history": self.history,
        }
        temp_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=STATE_PATH.parent,
                prefix=".state-", suffix=".tmp", delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                json.dump(data, temp_file, ensure_ascii=False, indent=2)
                temp_file.write("\n")
            temp_path.replace(STATE_PATH)
        except OSError:
            print("저장에 실패했습니다. 파일과 폴더의 쓰기 권한을 확인하세요.")
            return False
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

        self.needs_save = False
        return True

    def run(self):
        try:
            self.load_state()
            while True:
                self.show_menu()
                choice = read_number("선택: ", 1, 7)
                if choice == 1:
                    self.play()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.show_quizzes()
                elif choice == 4:
                    self.show_best_score()
                elif choice == 6:
                    self.delete_quiz()
                elif choice == 7:
                    self.show_history()
                else:
                    print("게임을 종료합니다.")
                    return
        except (KeyboardInterrupt, EOFError):
            print("\n입력이 중단되어 게임을 종료합니다.")
        finally:
            if self.needs_save and not self.save_state():
                print("이번 변경 내용을 파일에 저장하지 못했습니다.")


if __name__ == "__main__":
    QuizGame().run()
