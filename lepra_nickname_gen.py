import random
from lepra_shared import GlobalState, GRAPHOMANIA_NICK_QUEUE

# Элитные пулы


MALE_SINGLE_POOL = ["pagi", "Ublyadok", "navalny", "masacra", "uisky",  "Booch", "bujum", "cypa", "Shaman", "Kaban", "Udav", "Lein", "Herurg", "sly2m", "Karas", "Sokoty", "Kafka", "3meyc", "kiriyama", "secco", "zip", "pramax", "groul", "baduser", "vogel", "woodo", "Imoler", "911", "UHOCTPAHEZ", "cccp", "fel1x", "Bart", "ETO", "Rwanda11", "Koguro", "Omant", "fedor", "FelixR", "митяй", "minimalist", "Yo", "Porez", "emdin", "ankle", "Plintus", "haplishe", "chibis", "se7en", "Noel", "babich", "Gong", "Ilich", "Joshua5", "chaikovsky", "Шариков", "kvarik", "lunev", "lunix", "veneamin", "Spectre", "ElectoR", "wasp", "Distemper", "chilio", "AY", "strafe", "straifig", "Zuikov", "Tyler", "derevo", "T1mOn", "Cust", "bear_49", "adrianov", "Orange", "InQ", "Somadhy", "Re_Disco", "cgem", "ant", "MissBigTits", "Duran", "lumer", "Satan", "Ike", "maroon", "конь-в-пальто", "Рысьь", "Jazzuit", "uzhas", "varnav", "Кирилл", "Lokich", "Freak", "katarhis", "goatse", "ckkps", "Dishlovihlop", "OTKPOBEHHO", "resistor", "ShirMan", "vnizz", "Eugr", "tutabrain", "SENT", "pizdanucca", "ToxaZ", "Nurmamed", "bes-o-matik", "mugz", "ichik", "yachik", "Pchel", "Brook", "BAC51", "Raskalov", "jaybee", "Shady", "nagasaki", "abuzyarov", "kotenochkin", "I_Glukhov", "mama_p_zh", "bol_shvol", "OPKECTP", "Terkin", "che_guevara_ssa", "Fabeltier", "Felixoid", "VAMPiRE", "Elkranio", "Biba", "Boba", "Pupa", "Lupa", "Krueger", "zurfer", "pereehal", "Bruja_", "ЕГОР", "vovney", "palevo", "Biochemik", "zaedaet", "dilliago", "Fill", "KOCTOPE3", "fcuk", "5kg", "roMoceK", "anch", "dam65", "kermlinrussia", "APTEM", "freetonik", "0xFACE", "Fo", "sopraNo", "Lazarus", "3OTOB", "Nick78", "ncuHa", "Polkovnik", "reutersfriend", "yk", "nadoelo", "BNKTOP", "shu_shasu_shami", "Mapm", "rockamark", "TheWho", "Mertas", "de7ign", "skyfi", "YaRdrey", "Yanni", "Yancy9000", "scal", "C11H15NO2", "SENT", "Hitter", "жопаноги", "psydoc", "IIIopox", "Umgewandelt", "unab0mber", "Le", "JILOnOPA3PbIBATEJlb", "rekapitulant", "foreverlife", "deerua", "AsObAkAbOsA", "luminofer", "D_D", "eXtractor", "bodomic", "Bahamut", "KROKODIL_GASPA4O", "ABTO6YC", "Levin", "Serfer", "AKG", "ritual", "axxl", "pinstripe", "Isis", "DieHardDildo", "maxray", "tracid", "quakerman", "Gods_Tail", "Yand3x", "Mladen", "genn", "vitnick", "eMASTER", "katakl", "jetster", "Rt-I", "Yanno", "medvejonoks", "derebeobachter", "jus", "7AM", "lazycat", "hasbent", "marvie-42", "kapuletti", "barby", "toivo", "zasuli4", "teRmit", "mani", "Malleus", "seraf", "jes-ter", "oldman", "medstas", "joshi", "shurkala", "PentagramPro", "Arshloch", "orel", "konnitiva", "Petroff", "Quiproquoqus", "0x45455844", "digal", "fitzz", "marinchello", "spino", "gaichuk", "vetadol", "leningrado", "biohazard", "BGMT", "gravel", "Endios", "509", "sid_ze_head", "Psychotropan", "Sparklee", "kolorowe", "brammator", "OlegusMDH", "laar", "lavrentiy", "xiino", "Quakermann", "Catcher", "nu_hui_znaet", "Khmelic",  "imfuckingrabbit", "nokato", "tupaia", "m0ntana", "fl00r", "petr0vich", "Kvadrat", "irishman", "rpoM", "xozyainzooparka", "kofman", "dilesoft", "lazyqwe", "Erop_MaTblruH", "ikillbill", "thewatt", "three_sisters_3", "kir", "DeFactor", "Procatalipsis", "mataleao", "nuran", "yedrill", "cossackmsu", "KOIIETAH_PEIIKA", "CooLLeR", "PuG", "anyone-fun", "nugop", "Jupiter", "Delphis", "winterrain", "Oven", "parnas", "lisakov", "Inshalee", "Fabrika", "php", "ep5siL0n", "geezzzer", "bond", "izluchator", "Psychodozer", "Shaida", "oe2z", "Apelsinoff", "WolfeWOLF", "mOs", "zhno", "TangerineMaster", "dreamiurg", "colombo", "colombian", "LaFleur", "Elektrovenik", "FeoFUN", "TSIGOR", "ati_ff", "Paltus", "pampus", "evgenok", "faustmax", "OlegbI4", "udjin", "agent303", "Polkovnik", "recoilme", " HPABCTBEHHOCTb", "mandalavandalzzz", "Dzhel", "WereVarg", "etomoinick", "HitMan_ru", "tutabrain", "xoid", "T1M0N", "namreg", "fokusnik", "Pechorin", "Dee78", "maxray", "KPbISS", "romanoid", "ForJest", "DoveKill", "911", "roendoe", "sHiZz", "shiten", "Jcuken", "barmalini", "norpo", "reasonspace", "ABTO6YC", "vassabi", "Funtig", "diggerusha", "Shioheeru", "upStructure", "PVN", "Prontiol1", "zorba-buddha", "justMara", "theSPiRiT", "Chemodan", "orangedi", "bakulinnikita", "Noix", "robozombi", "Kong", "Len_in", "berdax", "neuroleptik", "yapplaka", "daPhoenix", "Prontiol1", "pawlentiy", "maxijazzz", "raz-dva-fari", "Freeze", "Incubus", "pustota_az", "ergib_dich", "Egorov", "korotkoff", "4ell", "asap", "5hin0bi", "ErbaAffetto", "crestana", "Schreibikus", "irishrover", "Twar", "i-zen", "ozelot", "unavailable", "keergeez", "sculder", "Apelsinoff", "Grey-Grey", "pel0tkin", "trancentral", "Bulwinkl", "nickolasm5", "bo_stitch", "Gelfand", "ludomaniac", "XEK", "Romanzo", "SoulReaver", "InsaneOfMe", "FoXXX", "spaniard", "faortto", "R2-D2", "Deekey", "kugel", "d71", "mataleao", "Hemml", "raven428", "Mapm", "pnac_spirit", "ynblpb", "tim_liri", "Zelenone", "onthefly", "Полуночный", "gizm0", "amon-mout", "Fry", "mani", "EMKOCTb", "XepMaH", "Illyaha", "ACTPOHABT", "NaFigator", "angrymonkey", "rubzn", "Casey", "el_Brujo", "crontab", "NoEndOutcry", "apchehov", "Riot_rus", "Mitrich", "ufolog", "konkere", "antivoland", "RedEvil", "ninjatuner", "StupidCasual", "Egoritch", "InDustReal", "Valent-eX", "SpikOlaf", "k1ngsize", "Goofee", "StanleyMos", "Korg", "DigitalBalda", "DoubleUAle", "Dobrinya", "Ibanez", "Ole_Bjoerndalen", "octocat", "T_I_M", "Param-param-pam", "apazhe", "Gopnique", "zayanc", "Demurg", "ptitzin", "encore", "C0BECTb", "LeproZorro", "shuraganjubas", "windowlicker", "vv____", "HuK-Xapgu", "romaha", "Wiedemann", "Agent007", "p10ner", "gsom", "Plagiator", "digitaldog", "Romanian", "panfilofff", "eBAKWAKA", "lesha28", "toxal", "cyberworm", "RedSmell", "larin", "jitkoff", "Vox_ex_Machina", "vsOdin", "Yani", "PsychodelEKS", "konfetas", "Fatbrain", "Zzayac", "Mephi", "katpyxa", "musketeer", "applejesus", "pizdanuque", "Ditfrid", "fixin", "DrKeeper", "grover", "zavhoz", "Andorro", "pihtachok", "vikram", "Elektron", "CoolHard", "B00StER", "einsturzende", "remizyaka", "bpunk", "sp-world", "Behemoth", "shturn", "konver", "R0land", "Procyrator", "AlexK100", "ebanucca", "volcano187", "mesequire", "le_big_mac", "hachipury", "morozOFF", "usachev", "aliF", "No_5", "aol", "asdffdsa", " ktonado", "iDen", "distemper303", "zhgun", "nexxt", "brutalshit", "PythonX", "Bubbblezzz", "GinToniC", "mongol", "vogulsamoed", "dergachoff", "KuT", "shaman007", "g_DiGGeR", "Intruder", "kpya3e", "JediRama", "opezdol", "mi55er", "pashchenko", "s7ang3r", "orange303", "andreyvo", "inkubus", "KaMa3", "qzzaargh", "Tenchi", "Kolbasevich"]
FEMALE_SINGLE_POOL = ["Iriska", "Mgla", "Event0077", "pravda", "vobla", "Mayakovskaya", "tetsuo", "busuka", "Mistina", "oleum", "Jey", "KT", "vikatine", "viketz", "masterica", "wunderbar", "Qumnica", "nataxxa", "Helengar", "FRANNI", "orlando", "Addict", "nasa", "nenastja", "rebrom", "Po11y", "pupsique", "Crocky", "nu", "e", "aringetic", "getback", "Bajka", "Venezia", "Aivengo", "Verta", "morganochka", "Tatiana", "OK-sanki", "firefox", "G-spot", "Orintaa", "zemlyanukhina", "золушка", "Есения", "Tetsuko", "Lethargia", "Мама-Чоли", "evidence", "discovery", "Lakshme", "rina-kizune", "Maks_Dashkov", "jul-jul", "Koziavka", "MareSole", "mariposa", "Strype", "Evidencia", "1o1a", "hellfreezer", "midnight", "cherryfox", "agnessa_ivanovna", "tyfelka", "vafelka", "ivana", "smolokom", "eve", "chepalova", "Helya", "rektif", "ligreego", "Lelka", "vasilisa", "poppyrosa", "Zaaaa", "diesell", "aisha", "MidNight", "INNA", "toyota", "Babasya", "Ziqel", "sasha-shwarz", "narkotik", "B1ixa", "snuff", "Venetzia", "Naghaina", "Miss_Evidence", "dzezva", "mimimimimimimimi", "yesfuture", "ashinara", "meteorolog", "Ainara", "IRIska", "katjka", "onepilot", "chatbizarre", "ShallBe"]

# Словари для двусложных
PREFIXES = ["dj", "skozlo", "pizdo", "zippy", "zloe", "ya", "aku", "Electro", "volf", "user", "a5ur", "kamuta", "anti", "crazy", "reason", "st", "needle", "Etinile", "Paper", "i", "miaou", "DMT", "Alice", "3", "Картофельный", "Ironia", "Vince", "med", "vedro", "Kot", "quick", "alcoholic", "tebe", "unreal", "cyber", "SKAZI", "tiger", "death",  "Meet", "jelly", "Soul", "macro", "mini", "SVETLO", "Azzkii", "UnoPunto", "Dr", "solong", "al", "FelixDa", "serge", "IRON", "Misha", "art", "yellow", "alex", "Cocaine", "Brooke", "hex", "anti", "Alice", "marea", "noch_na", "Suok", "fil_de", "mahatma", "Vsevolod", "beso", "Norbert", "Krokodilov", "vacuum", "jake", "starik", "tear", "atomic", "Jedi", "red", "Alexander", "Hugo", "Mihail", "Kobzon", "anusdestroyer", "cmapikocman", "romanzv", "stereo", "DILDO", "pavel", "Pohabych", "Pepyaka", "Misha", "Zapp", "Svinozubr", "zorba", "commander", "Sunduk", "Brigada", "Pyramid", "Klubnichnoe", "Baron", "lonely"]
SUFFIXES = ["jop", "huy", "pook", "max", "zlo", "frosya", "hirovata", "Felixx", "maple", "man", "seeker", "maker", "off", "banipa1", "Foster", "fang", "stradiol", "Wolf", "miaou", "DT", "bullet", "night", "rublya", "J7", "Crescendo", "Vega", "a-lion", "borsha", "BegemoTT", "justice", "friend", "interesno", "einger", "valenok", "cat", "art", "cactus", "ficus", "moroz", "рич", "TEPLO", "Sotona", "Zero", "Zoidberg", "celeste", "azif", "Housecat", "Savo", "Igor", "Rappe", "image", "head", "star", "TeddyBear", "Bond", "sex", "miaou", "internum", "fronte", "Suok", "Perse", "Ghandi", "Vodka", "o-matic", "Bebrueze", "Gena", "bong", "snake", "pohabych", "jerker", "gun", "Rama", "Hat", "Gaylord", "Stiglitz", "Kukuruza", "kun", "303", "404", "420", "69", "31337", "89", "kypum", "romanz", "silence", "TRON", "OMG", "Starik", "Misha", "Pepyaka", "venik", "Brannigan", "Pumba", "buddha", "keen", "Burunduk", "Zabvenje", "Head", "Milo", "Myxa", "coldcut"]

# Словарь существительных
ENGLISH_NOUNS = [

    "cat", "dog", "bird", "fish", "tree", "rock", "sky", "sun", "moon", "star",

    "wind", "rain", "snow", "fire", "ice", "cup", "book", "pen", "desk", "chair",

    "table", "door", "window", "floor", "wall", "roof", "car", "road", "bridge", "river",

    "lake", "ocean", "mountain", "hill", "valley", "forest", "field", "flower", "grass", "leaf",

    "root", "branch", "fruit", "seed", "cloud", "storm", "thunder", "lightning", "shadow", "light",

    "sound", "voice", "music", "song", "note", "picture", "image", "photo", "color", "shape",

    "circle", "square", "line", "point", "number", "word", "sentence", "story", "idea", "dream",

    "thought", "mind", "heart", "body", "hand", "foot", "eye", "ear", "nose", "mouth",

    "face", "hair", "skin", "bone", "blood", "time", "day", "night", "morning", "evening",

    "week", "month", "year", "moment", "place", "world", "earth", "space", "energy", "power", "random"

]

def generate_nickname(gender: str = "male", is_forced_enze=False, is_graphomania=False) -> str:
    """Генерирует никнейм согласно строгому приоритету."""
    if is_forced_enze: return "enze"
    
    # Теперь переменная is_graphomania определена через аргументы
    if is_graphomania:
        for nick in GRAPHOMANIA_NICK_QUEUE:
            if nick not in GlobalState.used_nicknames:
                GlobalState.used_nicknames.add(nick)
                return nick
    

    # 1. Односложные ники (по полу)
    pool = MALE_SINGLE_POOL if gender == "male" else FEMALE_SINGLE_POOL
    for nick in pool:
        if nick not in GlobalState.used_nicknames:
            GlobalState.used_nicknames.add(nick)
            return nick

    # 2. Двусложные ники (комбинаторика)
    # Попробуем найти случайную комбинацию из 1000 попыток, прежде чем сдаться
    for _ in range(1000):
        nick = f"{random.choice(PREFIXES)}_{random.choice(SUFFIXES)}"
        if nick not in GlobalState.used_nicknames:
            GlobalState.used_nicknames.add(nick)
            return nick

    # 3. English Nouns
    for noun in ENGLISH_NOUNS:
        if noun not in GlobalState.used_nicknames:
            GlobalState.used_nicknames.add(noun)
            return noun

    # 4. English Nouns + номера
    while True:
        nick = f"{random.choice(ENGLISH_NOUNS)}_{random.randint(100, 9999)}"
        if nick not in GlobalState.used_nicknames:
            GlobalState.used_nicknames.add(nick)
            return nick
