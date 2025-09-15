from typing import List, Callable, Optional
import random


# для демонстрации

def make_coin(p_heads: float, name: str = "") -> Callable[[], str]:
    def coin():
        # Если случайное число меньше p_heads -> выпал орёл ('H'),
        # иначе решка ('T').
        return 'H' if random.random() < p_heads else 'T'
    coin.__name__ = name or f"coin_{p_heads:.2f}"
    return coin


# input:
#   coins - список функций coin(), каждая имитирует один тип монеты
#   (каждый вызов coin() = один бросок этой монеты)
#   lam   - общий лимит бросков (lambda)
#
# output:
#   Индекс монеты в списке coins, которую мы выбираем как "5-ю по
#   обычности" среди антарктических (по нашим наблюдениям), либо None,
#   если бросков слишком мало и выбрать уверенно не вышло.
#
# алгоритм:
# 1) даём каждой монете немного бросков, чтобы понять,
# в какую сторону она смещена.
# - Антарктида (холодные): чаще орёл -> p(H) > 0.5
# - Сахара (тёплые):      чаще решка -> p(H) < 0.5
# берём монеты, где по наблюдениям p^(H) >= 0.5, как кандидатов Антарктиды.
#
# 2) сортируем этих кандидатов по "обычности" - это близость
# p^(H) к 0.5, то есть |p^ - 0.5|. Потом оставшиеся броски
# тратим в первую очередь на монеты вокруг 5-го места,
# чтобы именно там уточнить порядок.
#
# 3) возвращаем 5-ю по обычности
def find_diamond_coin_index(coins: List[Callable[[], str]], lam: int, verbose: bool = True) -> Optional[int]:
    n = len(coins)

    # проверяем базовые случаи: если монет нет или нет бросков - выходим
    if n == 0 or lam <= 0:
        if verbose:
            print("Ошибка. Нет монет или нет бросков")
        return None

    # эти два списка хранят статистику по монетам
    # heads[i] - сколько раз у i-й монеты выпал орёл
    # flips[i] - сколько раз бросали i-ю монету
    heads = [0] * n
    flips = [0] * n

    # функция одного броска для монеты i:
    # - вызывает coins[i]()
    # - переводит результат 'H'/'T' в 1/0
    # - обновляет счётчики
    def flip_once(i: int) -> int:
        x = coins[i]() # бросаем монету
        h = 1 if x in ('H', 'h', True, 1) else 0  # нормализуем к 1 (орёл) / 0 (решка)
        heads[i] += h # добавляем орла, если он выпал
        flips[i] += 1 # увеличиваем общее число бросков для этой монеты
        return h

    # оценка шанса орла p^(H) для монеты i по нашим наблюдениям:
    # p^ = (сколько раз выпал орёл) / (сколько раз мы бросали).
    # если мы ещё ни разу не бросали монету, считаем p^ = 0.5 (ничего не знаем).
    def phat(i: int) -> float:
        return heads[i] / flips[i] if flips[i] else 0.5

    # узнать сколько решек у монеты i
    def tails(i: int) -> int:
        return flips[i] - heads[i]

    used = 0 # сколько бросков уже потратили

    if verbose:
        print(f"Старт: всего монет = {n}, общий лимит бросков lambda = {lam}\n")


    # - если p^(H) >= 0.5, монета скорее "холодная" (Антарктида)
    # - иначе скорее "тёплая" (Сахара)
    base = max(1, lam // (3 * n))  # минимум по 1 броску на монету
    if verbose:
        print(f"1): даём базово по {base} бросков на монету (или меньше, если lambda закончим).")

    for r in range(base): # столько "раундов" по одной попытке на монету
        for i in range(n): # идём по каждой монете
            if used >= lam: # если броски закончились - выходим
                break
            h = flip_once(i) # делаем 1 бросок этой монеты
            used += 1
            if verbose:
                print(f"  бросок #{used:03d}: монета #{i:02d} -> {'H' if h else 'T'} (итого flips={flips[i]}, H={heads[i]})")
        if used >= lam:
            break

    # печатаем промежуточную сводку: сколько у кого бросков и чему равен p^
    if verbose:
        print("Итог Фазы 1 (наши оценки p^(H) по монетам):")
        for i in range(n):
            if flips[i] > 0:
                print(f"  монета #{i:02d}: flips={flips[i]:2d}, H={heads[i]:2d}, T={tails(i):2d}, p^={phat(i):.3f}")
            else:
                print(f"  монета #{i:02d}: flips= 0, p^=0.500 (ещё не бросали)")

    # выбираем кандидатов "Антарктида" по простому правилу:
    # p^(H) >= 0.5 (орлов не меньше, чем решек).
    antarctica = [i for i in range(n) if phat(i) >= 0.5]

    if verbose:
        print(f"Кандидаты Антарктида (p^(H) >= 0.5): {antarctica}")

    # может случиться, что из-за небольшого числа бросков мнения почти нет
    # (например, p^ у многих ≈ 0.5 или даже ниже случайно). если кандидатов < 5,
    # возьмём просто 5 монет с наибольшим p^(H)
    if len(antarctica) < 5:
        antarctica = sorted(range(n), key=lambda i: -phat(i))[:min(5, n)]
        if verbose:
            print("  Кандидатов меньше 5. Берём топ по наибольшим p^(H) как запасной вариант.")
            print(f"   Обновлённые кандидаты: {antarctica}")

    if not antarctica:
        if verbose:
            print(" Не получилось выделить ни одной антарктической монеты.")
        return None


    # 2) настройка вокруг 5 места
    #
    # теперь среди кандидатов Антарктиды надо найти 5-ю по обычности.
    # "обычность" = близость p^(H) к 0.5, то есть |p^ - 0.5| меньше -> обычнее.
    #
    # ошибка чаще всего случается возле границы 5-го места. поэтому
    # остаток бросков тратим в основном на монеты вокруг 5-й позиции
    # по текущему рейтингу обычности.
    if verbose:
        print("шаг 2: тратим оставшиеся броски на монеты вокруг 5-го места (чтобы точно не перепутать).")

    step = 0
    while used < lam and len(antarctica) > 1:
        step += 1

        # текущий рейтинг насколько обычная монета:
        # сортируем кандидатов по |p^ - 0.5| (чем ближе к 0.5, тем обычнее).
        ranked = sorted(antarctica, key=lambda i: abs(phat(i) - 0.5))

        # pятая по счёту позиция (с 0 начинается): индекс 4 - это 5-я.
        # вокруг неё нас интересуют позиции 3, 4, 5 (если они есть).
        focus_set = set()
        for j in (3, 4, 5):
            if 0 <= j < len(ranked):
                focus_set.add(ranked[j])

        # для понятности распечатаем верхнюю часть рейтинга:
        if verbose:
            print(f"\n- Шаг {step}: осталось бросков {lam - used}. Текущий топ обычных монет (до 8 штук):")
            for pos, coin_idx in enumerate(ranked[:8], start=1):
                print(f"  {pos:2d}) монета #{coin_idx:02d}: p^={phat(coin_idx):.3f}, |p^-0.5|={abs(phat(coin_idx)-0.5):.3f}")
            print(f"   Бросаем прицельно в монеты: {sorted(focus_set)}")

        # Бросаем по одному в каждую "фокусную" монету, пока есть лимит.
        for i in focus_set:
            if used >= lam:
                break
            h = flip_once(i)
            used += 1
            if verbose:
                print(f"     бросок #{used:03d}: монета #{i:02d} -> {'H' if h else 'T'} "
                      f"(теперь flips={flips[i]}, p^={phat(i):.3f})")

        # страховка: иногда имеет смысл чуть подбросить самую обычную
        # и монету около 6-й позиции, чтобы не пропустить резкие перестановки.
        if used < lam and len(ranked) > 6:
            for i in (ranked[0], ranked[6]):
                if used >= lam:
                    break
                h = flip_once(i)
                used += 1
                if verbose:
                    print(f"     страховка: монета #{i:02d} -> {'H' if h else 'T'} "
                          f"(flips={flips[i]}, p^={phat(i):.3f})")


    # 3) выбираем 5-ю по обычности среди холодных
    # если кандидатов меньше 5, берём самую обычную из того, что есть
    final_rank = sorted(antarctica, key=lambda i: abs(phat(i) - 0.5))

    if verbose:
        print("Финальный рейтинг антарктических по обычности:")
        for pos, i in enumerate(final_rank, start=1):
            print(f"  {pos:2d}) монета #{i:02d}: flips={flips[i]:2d}, H={heads[i]:2d}, T={tails(i):2d}, "
                  f"p^={phat(i):.3f}, |p^-0.5|={abs(phat(i)-0.5):.3f}")

    if len(final_rank) < 5:
        if verbose:
            print("  Нашлось меньше 5 кандидатов Антарктиды. Возвращаю лучшую из имеющихся (самую обычную).")
        return final_rank[-1] if final_rank else None

    answer = final_rank[4]  # это и есть пятая по обычности (индекс 4)
    if verbose:
        print(f"\n Ответ: монета #{answer} - 5-я по обычности среди антарктических (по нашим наблюдениям).")
    return answer



# демо:
if __name__ == "__main__":
    random.seed(7)

    # например: 6 "холодных" монет (p(H) > 0.5) и 6 "тёплых" (p(H) < 0.5)
    antarctic_ps = [0.70, 0.62, 0.58, 0.55, 0.53, 0.66]  # Антарктида - больше орлов
    sahara_ps    = [0.48, 0.45, 0.40, 0.35, 0.30, 0.49]  # Сахара - больше решек

    # перемешаем все монеты
    all_ps = antarctic_ps + sahara_ps
    random.shuffle(all_ps)

    # сделаем из вероятностей реальные "монеты" (функции)
    coins = [make_coin(p, name=f"coin_p={p:.2f}") for p in all_ps]

    # покажем скрытые p(H)
    for idx, p in enumerate(all_ps):
        group = "ANT" if p > 0.5 else "SAH"
        print(f"  #{idx:02d}: p(H)={p:.2f}  [{group}]")

    print("Запускаем алгоритм поиска… -\n")

    lam = 120

    ans_idx = find_diamond_coin_index(coins, lam, verbose=True)

    if ans_idx is not None:
        real_p = all_ps[ans_idx]
        grp = "ANT (холодная)" if real_p > 0.5 else "SAH (тёплая)"
        print(f"[ПРОВЕРКА] Выбрана монета #{ans_idx}, её настоящая p(H)={real_p:.2f}, группа: {grp}")
    else:
        print("[ПРОВЕРКА] Выбор не сделан (слишком мало бросков или не повезло с наблюдениями).")
