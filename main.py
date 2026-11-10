import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from questions import default_quizzes
from quiz import Quiz


STATE_PATH = Path(__file__).resolve().with_name("state.json")


def read_number(prompt, minimum, maximum):
    while True:
        raw = input(prompt).strip()
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
        self.needs_save = False

    def show_menu(self):
        print("\n=== 볼트빈 커피 퀴즈 ===")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")

    def play(self):
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return

        total = len(self.quizzes)
        correct = 0
        print(f"\n총 {total}문제를 시작합니다.")
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"\n[문제 {number}/{total}]")
            quiz.show()
            guess = read_number("정답 번호: ", 1, len(quiz.choices))
            if quiz.is_correct(guess):
                correct += 1
                print("정답입니다!")
            else:
                print(f"오답입니다. 정답은 {quiz.answer}번입니다. ({quiz.choices[quiz.answer - 1]})")

        score = correct * 100 // total
        print(f"\n결과: {total}문제 중 {correct}문제 정답 ({score}점)")
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            self.needs_save = True
            self.save_state()
            print(f"새 최고 점수입니다. ({score}점)")

    def add_quiz(self):
        print("\n새 퀴즈를 등록합니다.")
        question = read_text("문제: ")
        choices = []
        for number in range(1, 5):
            choices.append(read_text(f"선택지 {number}: "))
        answer = read_number("정답 번호: ", 1, 4)
        self.quizzes.append(Quiz(question, choices, answer))
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
            quizzes = [Quiz.from_dict(item) for item in raw["quizzes"]]
            best_score = raw["best_score"]
            if best_score is not None and (
                type(best_score) is not int or not 0 <= best_score <= 100
            ):
                raise ValueError("최고 점수는 0~100 사이의 정수여야 합니다.")
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
            print(f"저장한 퀴즈 {len(quizzes)}개와 점수 기록을 불러왔습니다.")

    def save_state(self):
        if not self.needs_save:
            return True

        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
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
                choice = read_number("선택: ", 1, 5)
                if choice == 1:
                    self.play()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.show_quizzes()
                elif choice == 4:
                    self.show_best_score()
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
