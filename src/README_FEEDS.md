Projektový deníček – gql_social / Feeds
Období: 12.–25. října 2026
Větev: 2026
Stav k 25. 10. 2026: Funkční a ručně otestovaná databázová vrstva, připravená ukázka na projektový den 26. 10. 2026.
Zadání a cíl
Cílem projektu je systém uživatelských feedů, v němž si uživatel vytvoří pojmenovaný přehled a určí, které entity (například projekty a granty) chce sledovat. Výsledný systém má zobrazovat související aktivity v časovém pořadí.

V této etapě jsem se zaměřila na databázovou vrstvu v Pythonu (SQLAlchemy 2.x) nad PostgreSQL. Navazuji na společný projekt gql_evolution a jeho architekturu GraphQL resolver → Service → DataLoader → DB model.
Databázové modely a vztahy
Model	Tabulka	Význam
FeedsModel	feeds	Konkrétní uživatelský feed: name, description, owner_id, color
FeedSourceModel	feed_sources	Sledovaná entita: feed_id, entity_id, entity_type_id, owner_id
FeedsTypeModel	feedtypes	Stromový číselník typů s parent_id, parent a children


Vztah FeedSource → Feed je řešen cizím klíčem feed_sources.feed_id → feeds.id a SQLAlchemy vztahem feed. Jeden feed může mít více zdrojů. Strom typů používá self-referenční cizí klíč feedtypes.parent_id → feedtypes.id.

feedtypes je v současné implementaci samostatný číselník: mezi konkrétním feedem a typem feedu zatím není definovaný cizí klíč. FeedSource.entity_type_id označuje typ sledované entity, nikoliv záznam v feedtypes.

Soubory modelů jsou v src/DBDefinitions/Domain_social/.
Postup práce a časová posloupnost commitů
Datum	Commity	Co se řešilo
12. 10. 2026	ec3587f, c3e853c	Ve společném repozitáři vznikl první návrh FeedsModel a začala úprava jeho atributů podle zadání. Tyto počáteční commity vytvořil spolužák.
14. 10. 2026	5f3fc0a, 6227680, 1be7be8	Upřesnění polí FeedsModel, tvorba a oprava názvu FeedsTypeModel, registrace modelů v __init__.py a odstranění chybného převzatého vztahu na události.
16. 10. 2026	f653aad	Doplnění FeedSourceModel, cizího klíče na feed a registrace všech tří modelů. Průběžné ruční testování databázových operací.
17. 10. 2026	2732985	Testy přes src.DBDefinitions.main a první demonstrační data v systemdata.json.
19. 10. 2026	74c387e	Oprava parent_id u podřízeného typu, aby skutečně ukazoval na existující rodičovský typ.
25. 10. 2026	72fc59b, 794ba6d, 83edd8b	Ladění spouštění seedu a práce se sessions, odstranění již nepotřebného feed_test.json, rozšíření systemdata.json a opravy chyb, které odhalilo spuštění CLI.


Problémy, na které jsem narazila, a jejich řešení
1. Registrace modelů a převzaté části školního vzoru. Při tvorbě typového modelu zůstalo původně nesprávné jméno třídy a ve FeedsModel vztah odkazující na události. Modely jsem upravila a zaregistrovala tak, aby je aplikace i testovací CLI našly.
2. Vztah rodič–potomek. V prvních datech měl podřízený typ špatně nastavený parent_id. Opravila jsem ho na UUID existujícího rodiče a ověřila načítání parent i children.
3. Import dat a UUID. Při ladění systemdata.json bylo potřeba hlídat syntaxi JSON i správný formát a návaznost UUID. Ověřila jsem, že každé feed_id odkazuje na existující feed a že strom používá správná rodičovská ID.
4. Chyba transakce při seedu. Při importu se objevilo A transaction is already begun on this Session. Původní sdílení jedné asynchronní session jsem nahradila vytvářením sessions přes async_sessionmaker. Import pak fungoval.
5. Chyby při úpravách spouštění. Objevila se chybná hodnota true místo Python True, chybějící odkaz na funkci seedu v testovacím CLI a po úpravě také IndentationError. Opravila jsem přepínač DEMODATA, oddělila import od CRUD příkazů a opravila odsazení. Poté CLI znovu fungovalo.
6. Staré testovací záznamy v databázi. Příkaz list četl také řádky vytvořené při dřívějších testech; soubor feed_test.json nebyl jejich aktuálním zdrojem. Nepotřebné záznamy jsem odstranila přes CRUD (nejprve závislé zdroje, potom feedy) a sjednotila demonstrační data do systemdata.json.
Demonstrační data a ověření funkčnosti
V systemdata.json jsou pro doménu Feeds připraveny:
- 5 typů tvořících dva stromy: Pracovni feedy → Projektove/Grantove feedy a Univerzitni feedy → Fakultni feedy;
- 4 feedy: Demo - moje projekty, Grantove vyzvy, Aktivity fakulty, Sledovane objekty;
- 9 zdrojů, přiřazených k těmto feedům pomocí feed_id.
UUID sledovaných entit a vlastníků jsou v těchto demonstračních datech ukázková; jejich existence v jiných službách nebyla ověřena.

Pro import všech demonstračních dat používám ve Windows CMD:
set "DEMODATA=True"
python -m src.DBDefinitions.seed
set "DEMODATA="
Bez zapnutého DEMODATA se standardně importují jen číselníky typu *TypeModel. Import běží odděleně od testovacího CRUD nástroje.

Ručně jsem ověřila operace CREATE, READ, UPDATE a DELETE u modelů, čtení stromových vazeb a načtení feedu ze zdroje. Příklady použitých příkazů:
python -m src.DBDefinitions.main Feeds list "{}"
python -m src.DBDefinitions.main FeedsType list "{\"include\":[\"parent\"]}"
python -m src.DBDefinitions.main FeedSource list "{\"include\":[\"feed\"]}"
V pgAdminu jsem zobrazila tabulky feeds, feed_sources a feedtypes, ověřila počty a vazby pomocí SQL JOIN. Dále jsem přes Python CLI vytvořila nový feed a nový FeedSource, ověřila jejich uložení přímo v PostgreSQL a následně testovací záznamy bezpečně smazala. Scénář živé ukázky jsem si vyzkoušela nanečisto.
Co se zatím nepodařilo dokončit a další postup
Zadání pokrývá celý GraphQL systém, ale popsaná etapa řeší především databázi. Zatím nejsou pro doménu Feeds dokončené vlastní DataLoadery, Services, GraphQL typy a resolvery, GraphQL query/mutace, načítání a časové řazení skutečných aktivit, autorizace, chybové kódy ani integrační ověření federace. Tyto části musí následovat při zachování architektury resolver → Service → Loader → DBModel.

Existující obecné testy a ruční CRUD kontrola neprokazují požadované automatické pokrytí 95 %. Dalším krokem je napsat cílené unit/integration testy pro Feeds, spouštět je nad oddělenou testovací databází a změřit coverage. Ověření WhoAmIExtension, transakčních mutací, GraphQL popisů, filtrů a publikace Docker image rovněž zůstává předmětem další práce.
Zhodnocení
Nejdůležitějším výsledkem je funkční základ databázové části: modely jsou registrované, stromové vazby i vztah FeedSource → Feed fungují, demonstrační data je možné importovat a CRUD operace jsem ověřila také přímo v pgAdminu. Při práci jsem se naučila rozlišovat data z JSON souboru od záznamů již uložených v databázi, správně používat UUID a cizí klíče, pracovat s asynchronními databázovými sessions a kontrolovat změny pomocí Git historie.

Projektový den 26. 10. 2026: průběh a zpětnou vazbu doplním po prezentaci.