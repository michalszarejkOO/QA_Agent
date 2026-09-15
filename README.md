# QA_Agent

Przegląd agenta i skilli, którymi steruje Claude Code w roli QA. To repo jest
**źródłem prawdy** — zawiera realne pliki, nie symlinki. `./setup.sh` podpina je
symlinkami pod `~/.claude/skills/` i `~/.claude/agents/`, żeby były widoczne dla
Claude Code z dowolnego projektu na tej maszynie; edycja w repo albo przez symlink
to fizycznie ten sam plik.

## Setup na nowej maszynie / po sklonowaniu

```
git clone <ten-remote> && cd QA_Agent
./setup.sh
```

Podepnie `agents/qa-tester.md` i każdy folder z `skills/` pod `~/.claude/` (albo pod
`$CLAUDE_CONFIG_DIR`, jeśli ustawiony). Jeśli pod tymi ścieżkami jest już coś
innego, `setup.sh` robi kopię `.bak` przed podmianą na symlink — bezpieczne do
wielokrotnego uruchomienia.

Następnie utwórz `~/.claude/environments/` (globalne, gitignored, nigdy nie trafia
do żadnego repo) i dorzuć tam własne pliki `<produkt>-<env>.json` z danymi
dostępowymi do swoich środowisk staging — kształt i pola opisane w
[`environments.example/`](./environments.example/). `environments/` w tym repo to
tylko wygodny symlink do tamtej lokalizacji, żeby dało się ją podejrzeć z poziomu
projektu.

## Zawartość

- `environments/` (symlink do `~/.claude/environments/`, w `.gitignore` — nigdy nie
  commitować) — per-produkt/per-środowisko config z danymi dostępowymi (Basic Auth,
  login testowy) do pinowanych środowisk staging, jeden plik JSON na produkt/env —
  np. `osh-staging.json` dla ticketów o prefiksie `OSH-*`. Globalna lokalizacja =
  ten sam config widoczny dla `qa-tester`/`testing-bruno-api` niezależnie od tego, w
  jakim projekcie/repo akurat pracujesz — dochodzi nowa aplikacja, dorzucasz kolejny
  plik `<produkt>-<env>.json` z polem `ticketPrefixes`, i oba automatycznie go
  znajdą po prefiksie ticketu albo repo, zamiast czekać na ręczne podanie danych w
  trakcie sesji. Zobacz [`environments.example/`](./environments.example/) po
  dokładny kształt JSON-a (osobne przykłady dla produktu z UI i dla produktu z
  kolekcją Bruno).

- `agents/qa-tester.md` — subagent wykonujący QA na żywej aplikacji na podstawie
  ticketu Jira, diffu PR-a i (opcjonalnie) designu Figma — Playwright dla apki
  webowej, `agent-device` (skill `testing-mobile-apps`) dla apki mobilnej
  iOS/Android. Nie edytuje kodu, nie publikuje nic w Jirze bez wyraźnej zgody
  użytkownika.
- `skills/writing-test-cases/` — pisze statyczne test case'y (Title / Preconditions /
  Steps to reproduce / Expected result) z ticketu/diffu, niezależnie od egzekucji.
  Zbindowany do `qa-tester` (krok "Derive scenarios").
- `skills/reporting-bugs/` — szkicuje zgłoszenie buga (Title / Steps to reproduce /
  Expected / Actual). Zbindowany do `qa-tester` (krok "Bug report draft"). Nigdy sam
  nie publikuje — tylko szkic.
- `skills/testing-mobile-apps/` — odpowiednik egzekucji Playwrightowej, ale dla apek
  mobilnych iOS/Android przez `agent-device` (Callstack): jak podłączyć
  symulator/emulator/fizyczne urządzenie, konwersja pikseli zrzutu na punkty przy
  `press`, weryfikacja "martwego przycisku" zarówno przez ref jak i współrzędne (żeby
  złapać realne rozjazdy accessibility hit-frame zamiast raportować fałszywy alarm),
  oraz osobny plik referencyjny na jednorazowy setup podpisywania dla fizycznego
  iPhone'a. Celowo zawężony do mobile — `agent-device` umie też macOS/TV/web, ale ten
  skill się do tego nie miesza. Zbindowany do `qa-tester` (krok "Execute" — gałąź
  "iOS/Android mobile app").
- `skills/preparing-refinement-questions/` — generuje pytania do sesji refinementu na
  podstawie ticketu Jira. **Samodzielny skill, celowo niezbindowany** do żadnego
  agenta (dotyczy etapu przed dostarczeniem feature'a, więc `qa-tester` by go nigdy
  nie użył — bindowanie tylko podnosiłoby koszt kontekstu przy każdym teście).
- `skills/testing-bruno-api/` — uruchamia kolekcję Bruno danego repo przez Bruno CLI
  na żywym środowisku, eksportuje ją do zipa, opcjonalnie odświeża stronę-tracker w
  Confluence (dołączając zip jako załącznik) i generuje raport pass/fail gotowy do
  wklejenia w komentarz Jiry. **Samodzielny, celowo niezbindowany** do `qa-tester` —
  to testowanie API na poziomie kolekcji, nie manualne QA na żywej appce. Product-
  agnostic: który repo/kolekcja i (jeśli dotyczy) która strona Confluence, bierze z
  `environments/<produkt>-<env>.json` → klucz `bruno` (repo, collectionPath,
  defaultEnvironment, knownCaveats, opcjonalnie confluence). Przeniesiony i uogólniony
  z repo-lokalnego `.claude/skills/testing-bruno-api` w `mowaamah-application-api` —
  tamten był zaszyty pod jeden projekt (ścieżka `/bruno`, nazwa zipa, jedna strona
  Confluence); tu te fakty żyją w `environments/mowaamah-demo.json`, a skill działa
  dla dowolnego repo z kolekcją Bruno.

## Skąd to się wzięło

Powstało podczas sesji QA na tickecie OSH-1270 (PR #209, `takamol-osh-portal`) — po
drodze napotkaliśmy kilka realnych ograniczeń (autoryzacja Atlassiana do złego site'u,
prywatne repo na Bitbuckecie, nietypowy login, bramka płatności SADAD), które
przełożyły się na konkretne poprawki w `qa-tester.md`, oraz na pytanie, co z tego
powinno być osobnym, wielokrotnego użytku skillem.

`skills/testing-mobile-apps/` powstał po sesji eksploracyjnej na aplikacji mowaamah
(iOS, fizyczny iPhone). Jednorazowy setup podpisywania (Developer Mode urządzenia i
macOS, certyfikat z lokalnym kluczem w Xcode, rejestracja UDID w koncie deweloperskim)
zajął większość sesji i trafił do osobnego pliku referencyjnego, żeby kolejne razy
nie odtwarzały go metodą prób i błędów. Dwie rzeczy z tamtej sesji, które i tak
warto znać: `agent-device`'owy daemon trzyma zmienne środowiskowe z chwili własnego
startu (późniejszy `export` ich nie dotyka — trzeba go ubić i odpalić na nowo), a
`press <x> <y>` przyjmuje punkty iOS, nie piksele zrzutu ekranu — pomylenie jednostek
raz doprowadziło do fałszywego zgłoszenia "martwego przycisku", który w
rzeczywistości działał poprawnie po dotknięciu we właściwym miejscu (a i tak ujawnił
realny błąd: jego accessibility hit-frame był przesunięty względem widocznej
pozycji — poważne w apce dla osób z niepełnosprawnościami).

## Jak to działa razem

`qa-tester` ma w swoim frontmatterze:

```yaml
skills:
  - writing-test-cases
  - reporting-bugs
  - testing-mobile-apps
```

Te trzy skille ładują się w pełni przy każdym uruchomieniu agenta (nie na zasadzie
routingu opisowego) i są używane wewnątrz jego własnej procedury —
`testing-mobile-apps` tylko na gałęzi "cel to apka mobilna, nie URL". `preparing-
refinement-questions` wywołuje się wprost, niezależnie od `qa-tester` — np. "przygotuj
pytania do refinementu dla OSH-XXXX".
