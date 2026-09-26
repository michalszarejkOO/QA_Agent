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
  ten sam config widoczny dla `qa-tester`/`testing-api` niezależnie od tego, w jakim
  projekcie/repo akurat pracujesz — dochodzi nowa aplikacja, dorzucasz kolejny plik
  `<produkt>-<env>.json` z polem `ticketPrefixes`, i oba automatycznie go znajdą po
  prefiksie ticketu albo repo, zamiast czekać na ręczne podanie danych w trakcie
  sesji. Zobacz [`environments.example/`](./environments.example/) po dokładny
  kształt JSON-a (osobne przykłady dla produktu z UI i dla produktu z kolekcją API).

- `agents/qa-tester.md` — subagent wykonujący QA na żywej aplikacji na podstawie
  ticketu Jira, diffu PR-a i (opcjonalnie) designu Figma — egzekucję na żywej
  appce (Playwright dla weba, `agent-device` dla iOS/Android) delegowaną w całości
  do skilla `testing-apps`. Nie edytuje kodu, nie publikuje nic w Jirze bez
  wyraźnej zgody użytkownika.
- `skills/writing-test-cases/` — pisze statyczne test case'y (Title / Preconditions /
  Steps to reproduce / Expected result) z ticketu/diffu, niezależnie od egzekucji.
  Zbindowany do `qa-tester` (krok "Derive scenarios").
- `skills/reporting-bugs/` — szkicuje zgłoszenie buga (Title / Steps to reproduce /
  Expected / Actual). Zbindowany do `qa-tester` (krok "Bug report draft"). Nigdy sam
  nie publikuje — tylko szkic.
- `skills/testing-apps/` — egzekucja scenariuszy na żywej appce: jeden skill, jeden
  wybór adaptera po kształcie targetu (URL → web/Playwright, bundle id/nazwa
  urządzenia → mobile/`agent-device`), zamiast dwóch osobnych miejsc na tę samą
  logikę. Adapter web (`references/adapters/web.md`) niesie to, co wcześniej było
  wpisane inline w `qa-tester.md`: świeża sesja przy każdym uruchomieniu,
  network-przed-klikaniem, dyscyplina zrzutu ekranu przed oceną wyniku. Adapter
  mobile (`references/adapters/mobile.md`, dawny samodzielny skill
  `testing-mobile-apps`) niesie mechanikę `agent-device`: konwersja pikseli zrzutu
  na punkty przy `press`, weryfikacja "martwego przycisku" zarówno przez ref jak i
  współrzędne (żeby złapać realne rozjazdy accessibility hit-frame zamiast
  raportować fałszywy alarm), gotcha z demonem trzymającym stare zmienne
  środowiskowe, oraz osobny plik referencyjny na jednorazowy setup podpisywania dla
  fizycznego iPhone'a. Reguły wspólne dla obu platform (real-account/real-payment
  boundary, "nie oceniaj bez obejrzenia zrzutu") żyją raz, w głównym `SKILL.md`, nie
  w każdym adapterze osobno. Celowo zawężony do web+mobile (iOS/Android) —
  `agent-device` umie też macOS/TV, ale ten skill się do tego nie miesza. Zbindowany
  do `qa-tester` (krok "Execute"), a mobile adapter też wywoływalny wprost do
  dogfoodingu bez pełnego kontekstu ticketu/PR.
- `skills/preparing-refinement-questions/` — generuje pytania do sesji refinementu na
  podstawie ticketu Jira. **Samodzielny skill, celowo niezbindowany** do żadnego
  agenta (dotyczy etapu przed dostarczeniem feature'a, więc `qa-tester` by go nigdy
  nie użył — bindowanie tylko podnosiłoby koszt kontekstu przy każdym teście).
- `skills/testing-api/` — uruchamia kolekcję testów API (Bruno, Postman lub
  Insomnia) danego repo przez CLI tego narzędzia na żywym środowisku, eksportuje ją
  do zipa, opcjonalnie odświeża stronę-tracker w Confluence (dołączając zip jako
  załącznik) i generuje raport pass/fail gotowy do wklejenia w komentarz Jiry.
  **Samodzielny, celowo niezbindowany** do `qa-tester` — to testowanie API na
  poziomie kolekcji, nie manualne QA na żywej appce. Product- i tool-agnostic: który
  repo/kolekcja/klient i (jeśli dotyczy) która strona Confluence, bierze z
  `environments/<produkt>-<env>.json` → klucz `api` (pole `client`: `bruno` |
  `postman` | `insomnia`, plus repo, collectionPath, defaultEnvironment,
  knownCaveats, opcjonalnie confluence). Mechanika specyficzna dla danego narzędzia
  (jak spakować kolekcję, dokładna komenda CLI, gdzie żyją adnotacje/caveats per
  case) żyje w jednym pliku adaptera per klient (`references/adapters/{bruno,
  postman,insomnia}.md`); wszystko inne (szablon raportu, publikacja do Confluence,
  wykrywanie stateful case'ów) jest wspólne i niepowtórzone. Historycznie: skill
  powstał jako `testing-bruno-api`, przeniesiony i uogólniony z repo-lokalnego
  `.claude/skills/testing-bruno-api` w `mowaamah-application-api` (tamten był
  zaszyty pod jeden projekt); Postman i Insomnia dołożone jako kolejne adaptery, gdy
  okazało się, że różne projekty używają różnych klientów API i dwa/trzy osobne
  skille duplikowałyby tę samą logikę raportowania.

- `skills/routing-qa-tickets/` — samodzielny skill wywoływany na samym początku, gdy
  request niesie tylko goły ticket Jira i/albo link do PR-a, bez wskazania, czy zmiana
  jest front- czy backendowa. Sprawdza config w `~/.claude/environments/` (sam kształt
  configu — tylko `api` albo tylko `surfaces` — czasem rozstrzyga od razu), a jeśli nie,
  patrzy na tanie sygnały (etykiety/komponent ticketu, lista zmienionych plików z PR-a,
  bez pełnego diffu) i klasyfikuje backend/frontend, a dla frontendu dodatkowo web/
  mobile. Backend → przekazuje dalej do `testing-api` bez zmian. Frontend → dokłada
  konkretny target (web: `surfaces.*.appUrl` z configu; mobile: pyta o device/bundle id,
  bo obecny kształt configu go nie niesie) i przekazuje do `qa-tester`. Rozjazd sygnałów
  (dotknięte ścieżki wyglądają i na backend, i na frontend) albo ich brak → nie zgaduje,
  pyta użytkownika. Nie duplikuje niczyjego kontekstu — samo tylko klasyfikuje i
  przekazuje dalej.

## Skąd to się wzięło

Powstało podczas sesji QA na tickecie OSH-1270 (PR #209, `takamol-osh-portal`) — po
drodze napotkaliśmy kilka realnych ograniczeń (autoryzacja Atlassiana do złego site'u,
prywatne repo na Bitbuckecie, nietypowy login, bramka płatności SADAD), które
przełożyły się na konkretne poprawki w `qa-tester.md`, oraz na pytanie, co z tego
powinno być osobnym, wielokrotnego użytku skillem.

`skills/testing-apps/`'owy mobile adapter powstał po sesji eksploracyjnej na
aplikacji mowaamah (iOS, fizyczny iPhone) — początkowo jako samodzielny skill
`testing-mobile-apps`. Jednorazowy setup podpisywania (Developer Mode urządzenia i
macOS, certyfikat z lokalnym kluczem w Xcode, rejestracja UDID w koncie deweloperskim)
zajął większość sesji i trafił do osobnego pliku referencyjnego, żeby kolejne razy
nie odtwarzały go metodą prób i błędów. Dwie rzeczy z tamtej sesji, które i tak
warto znać: `agent-device`'owy daemon trzyma zmienne środowiskowe z chwili własnego
startu (późniejszy `export` ich nie dotyka — trzeba go ubić i odpalić na nowo), a
`press <x> <y>` przyjmuje punkty iOS, nie piksele zrzutu ekranu — pomylenie jednostek
raz doprowadziło do fałszywego zgłoszenia "martwego przycisku", który w
rzeczywistości działał poprawnie po dotknięciu we właściwym miejscu (a i tak ujawnił
realny błąd: jego accessibility hit-frame był przesunięty względem widocznej
pozycji — poważne w apce dla osób z niepełnosprawnościami). `testing-mobile-apps`
żył potem osobno od Playwrightowej egzekucji webowej, która była wpisana inline w
`qa-tester.md` — asymetria bez powodu, więc obie trafiły razem do `skills/
testing-apps/` jako dwa adaptery jednego skilla, tym samym wzorcem co później
`testing-api` dla Bruno/Postman/Insomnia.

## Jak to działa razem

`qa-tester` ma w swoim frontmatterze:

```yaml
skills:
  - writing-test-cases
  - reporting-bugs
  - testing-apps
```

Te trzy skille ładują się w pełni przy każdym uruchomieniu agenta (nie na zasadzie
routingu opisowego) i są używane wewnątrz jego własnej procedury — `testing-apps`
w kroku "Execute", samo wybierając adapter web/mobile po kształcie targetu.
`preparing-refinement-questions` wywołuje się wprost, niezależnie od `qa-tester` — np. "przygotuj
pytania do refinementu dla OSH-XXXX".
