from questions import default_quizzes


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


class QuizGame:
    def __init__(self):
        self.quizzes = default_quizzes()

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
                print(f"오답입니다. 정답은 {quiz.answer}번 {quiz.choices[quiz.answer - 1]}입니다.")

        score = correct * 100 // total
        print(f"\n결과: {total}문제 중 {correct}문제 정답 ({score}점)")

    def run(self):
        try:
            while True:
                self.show_menu()
                choice = read_number("선택: ", 1, 5)
                if choice == 1:
                    self.play()
                elif choice == 5:
                    print("게임을 종료합니다.")
                    return
                else:
                    print("아직 준비 중인 메뉴입니다.")
        except (KeyboardInterrupt, EOFError):
            print("\n입력이 중단되어 게임을 종료합니다.")


if __name__ == "__main__":
    QuizGame().run()
