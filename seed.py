"""
Script para poblar la base de datos con destinos y articulos de ejemplo.
Uso: python seed.py
"""
from models import db, Destination, BlogPost

DESTINATIONS = [
    # AVENTURA
    {
        'name': 'Machu Picchu',
        'country': 'Peru',
        'description': 'La ciudadela inca perdida en las nubes de los Andes peruanos.',
        'long_description': '''Machu Picchu es una de las maravillas del mundo moderno y el sitio arqueologico mas visitado de America del Sur. Construida alrededor del siglo XV por el Imperio inca, esta ciudadela se encuentra a 2.430 metros sobre el nivel del mar, entre las montanas de los Andes.

El complejo arquitectonico incluye templos, palacios y terrazas agricolas que demuestran el avanzado conocimiento de los incas en ingenieria y astronomia. La Intihuatana, el Templo del Sol y el Salon de las Tres Ventanas son algunos de los puntos mas destacados.

Para llegar, la mayoria de los visitantes toman el tren desde Cusco hasta Aguas Calientes, y luego un bus hasta la entrada del sitio. Tambien es posible hacer el famoso Camino Inca, una caminata de 4 dias que culmina en la Puerta del Sol con vistas impresionantes de la ciudadela.

La mejor epoca para visitar es durante la estacion seca, entre mayo y octubre. Se recomienda llegar temprano para evitar las multitudes y disfrutar de la niebla matutina que rodea las ruinas.''',
        'image_url': 'https://images.unsplash.com/photo-1526392060635-9d6019884377?auto=format&fit=crop&w=800&q=80',
        'category': 'aventura',
        'emoji': '🏔️',
        'price_range': '$$',
    },
    {
        'name': 'Patagonia',
        'country': 'Argentina / Chile',
        'description': 'Glaciares imponentes, torres de granito y paisajes salvajes en el fin del mundo.',
        'long_description': '''La Patagonia es uno de los ultimos grandes desiertos del planeta, compartido entre Argentina y Chile. Con una superficie de casi un millon de kilometros cuadrados, ofrece paisajes que van desde estepas ventosas hasta bosques templados, glaciares y fiordos.

El Parque Nacional Torres del Paine, en el lado chileno, es el destino mas icónico de la region. Sus tres torres de granito que se elevan abruptamente desde la pampa son una de las imagenes mas reconocibles del continente. El Circuito W y el trekking completo son experiencias que los amantes del senderismo no pueden perderse.

En el lado argentino, El Calafate es la puerta de entrada al Glaciar Perito Moreno, uno de los pocos glaciares del mundo que sigue creciendo. Ver el desprendimiento de bloques de hielo es un espectaculo natural unico.

La mejor epoca para visitar es entre noviembre y marzo, durante el verano austral. El clima es siempre impredecible, por lo que se recomienda llevar ropa para todo tipo de condiciones.''',
        'image_url': 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=800&q=80',
        'category': 'aventura',
        'emoji': '🌿',
        'price_range': '$$$',
    },
    {
        'name': 'Tokio',
        'country': 'Japon',
        'description': 'Una megatropolis donde la tradicion milenaria y la vanguardia tecnologica conviven en perfecta armonia.',
        'long_description': '''Tokio es la ciudad mas poblada del mundo y una de las mas fascinantes. Capital de Japon desde el siglo XVII, cuando era conocida como Edo, hoy es un gigante urbano de 37 millones de habitantes que sorprende a cada paso.

Los barrios de Shibuya y Shinjuku representan el Tokio moderno, con sus rascacielos, pantallas gigantes y el famoso cruce de Shibuya donde miles de personas cruzan desde todos los angulos simultaneamente. En contraste, Asakusa conserva la esencia del Tokio tradicional con el templo Senso-ji y sus calles de tiendas artesanales.

La gastronomia tokiota es legendaria: tiene mas estrellas Michelin que cualquier otra ciudad del mundo. Desde ramen y sushi hasta kaiseki y wagyu, cada barrio ofrece una propuesta culinaria distinta.

Los cerezos en flor (sakura) durante abril transforman la ciudad en un espectaculo de color rosado. Los jardines de Shinjuku Gyoen y el parque Ueno son los mejores puntos para disfrutarlos.''',
        'image_url': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80',
        'category': 'aventura',
        'emoji': '🗼',
        'price_range': '$$$',
    },
    {
        'name': 'Nueva York',
        'country': 'Estados Unidos',
        'description': 'La ciudad que nunca duerme. Energia, diversidad y cultura en cada esquina.',
        'long_description': '''Nueva York es quizas la ciudad mas famosa del mundo y con razon. Con sus 8 millones de habitantes, 5 boroughs y cientos de vecindarios, cada visita revela algo nuevo.

Manhattan es el corazon de la ciudad, hogar del Central Park, el Empire State Building, el MoMA, Broadway y el barrio de SoHo. El Highline, un parque elevado construido sobre vias ferreas en desuso, es uno de los proyectos urbanos mas innovadores del mundo.

Brooklyn ofrece una perspectiva mas relajada y artistica de la ciudad. El Puente de Brooklyn, DUMBO, Williamsburg y el Parque Prospect son imperdibles. Desde la orilla de Brooklyn se obtiene la mejor vista del skyline de Manhattan.

Para moverse, el metro funciona las 24 horas y conecta todo. Se recomienda conseguir una MetroCard. Los precios en NYC son altos, pero hay muchos museos gratuitos y la vida de barrio es completamente accesible.''',
        'image_url': 'https://images.unsplash.com/photo-1485871981521-5b1fd3805eee?auto=format&fit=crop&w=800&q=80',
        'category': 'aventura',
        'emoji': '🗽',
        'price_range': '$$$',
    },

    # RELAX
    {
        'name': 'Maldivas',
        'country': 'Republica de Maldivas',
        'description': 'Atolones de arena blanca, aguas cristalinas y bungalows sobre el mar en el Indico.',
        'long_description': '''Las Maldivas es un archipielago de 1.200 islas coralinas en el oceano Indico, conocido por sus aguas transparentes de color turquesa y sus arrecifes de coral. Es uno de los destinos de lujo mas cotizados del mundo y una postal de paraiso tropical.

Cada resort ocupa su propia isla privada o parte de un atolon, lo que garantiza privacidad y exclusividad. Los bungalows sobre el agua (overwater villas) son su imagen mas caracteristica: habitaciones con suelo de cristal que permiten ver el lecho marino desde la cama.

El buceo y el snorkel son las actividades estrella. Los arrecifes alojan una biodiversidad marina increible: tiburones ballena, mantarrayas, tortugas y miles de especies de peces de colores. El mejor buceo se encuentra en North Male Atoll y Ari Atoll.

Las Maldivas tienen uno de los indices de riqueza de coral mas altos del planeta, aunque vulnerable al cambio climatico. Visitar estos atolones es tambien conectarse con la urgencia de preservarlos.''',
        'image_url': 'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=800&q=80',
        'category': 'relax',
        'emoji': '🏝️',
        'price_range': '$$$',
    },
    {
        'name': 'Bali',
        'country': 'Indonesia',
        'description': 'La isla de los dioses: templos, arrozales en terrazas y una cultura espiritual unica.',
        'long_description': '''Bali es la isla mas visitada de Indonesia y uno de los destinos mas magicos del mundo. Su combinacion de playas tropicales, selvas densas, terrazas de arroz esculpidas en las colinas y una cultura hindu profundamente arraigada la convierte en un lugar unico.

Ubud, en el corazon de la isla, es el centro cultural y espiritual. El Palacio Real de Ubud, los mercados de artesanias, las escuelas de yoga y los spas de bienestar atraen a viajeros que buscan reconectar consigo mismos. El bosque de los monos y el templo de Pura Taman Saraswati son visitas obligadas.

Seminyak y Canggu son los epicentros del surf y la vida nocturna. La ola de Uluwatu es famosa en todo el mundo entre los surfistas, y el templo del mismo nombre, construido sobre un acantilado de 70 metros, ofrece atardeceres espectaculares con danzas Kecak.

Los retiros de yoga y meditacion son una de las principales razones por las que las personas vuelven una y otra vez a Bali. La combinacion de ambiente tranquilo, gastronomia saludable y naturaleza exuberante es difícil de igualar.''',
        'image_url': 'https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?auto=format&fit=crop&w=800&q=80',
        'category': 'relax',
        'emoji': '🌺',
        'price_range': '$$',
    },
    {
        'name': 'Santorini',
        'country': 'Grecia',
        'description': 'Casas blancas con cupulas azules sobre el borde de un volcan dormido en el mar Egeo.',
        'long_description': '''Santorini es la isla mas romantica del Mediterraneo y una de las mas fotografiadas del mundo. Formada por la explosion de un super volcan hace 3.600 anos, la isla tiene una forma de medialuna que rodea una caldera marina de aguas profundas y de un azul intenso.

Oia es el pueblo mas famoso, conocido por sus casas encaladas, iglesias de cupula azul y los atardeceres mas espectaculares de Europa. Las calles estrechas, las terrazas con vistas al volcan y los restaurantes de marisco crean una atmosfera irresistible. Llegar temprano es fundamental para conseguir el mejor lugar para el sunset.

Fira, la capital, combina el encanto tradicional con una oferta de bares, restaurantes y vida nocturna animada. Desde aqui parten los teleféricos y los barcos para explorar la caldera.

La playa de Perivolos tiene arena oscura volcanica, una característica unica de la isla. El vino Assyrtiko, producido en las vinas de Santorini, es uno de los mejores de Grecia y maridado con el frescura marina es una experiencia sensorial completa.''',
        'image_url': 'https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=800&q=80',
        'category': 'relax',
        'emoji': '🌅',
        'price_range': '$$$',
    },
    {
        'name': 'Cancun',
        'country': 'Mexico',
        'description': 'Playas de arena blanca, mar turquesa y la magia de la cultura maya en el Caribe mexicano.',
        'long_description': '''Cancun es el destino turistico mas visitado de Mexico y uno de los mas populares del mundo. Ubicada en el estado de Quintana Roo, en el extremo norte de la Peninsula de Yucatan, combina playas paradisiacas con la riqueza cultural de la civilizacion maya.

La Zona Hotelera concentra los grandes resorts all-inclusive frente al mar Caribe. La playa Delfines, Playa Forum y Playa Tortugas son las mas accesibles y frecuentadas. El agua es de un turquesa intenso y la temperatura es perfecta casi todo el ano.

A menos de una hora se encuentra Chichen Itza, una de las Siete Maravillas del Mundo Moderno. El Templo de Kukulkan, el Observatorio y el Juego de Pelota son testimonio de la avanzada civilizacion maya. También estan las ruinas de Tulum, sobre un acantilado frente al mar, que combinan historia y playa de manera unica.

La gastronomia yucateca es extraordinaria: cochinita pibil, tacos de canasta, ceviche de camaron y las marquesitas son infaltables. El cenote Ik Kil y el parque Xcaret son actividades familiares muy recomendadas.''',
        'image_url': 'https://images.unsplash.com/photo-1552074284-5e88ef1aef18?auto=format&fit=crop&w=800&q=80',
        'category': 'relax',
        'emoji': '🌊',
        'price_range': '$$',
    },

    # CULTURA
    {
        'name': 'Roma',
        'country': 'Italia',
        'description': 'La Ciudad Eterna: dos milenios de historia, arte y gastronomia en cada esquina.',
        'long_description': '''Roma es una de las ciudades mas fascinantes del mundo, donde la historia antigua convive con el caos vibrante de una ciudad moderna. Capital de Italia y sede del Vaticano, acumula mas sitios del Patrimonio de la Humanidad que cualquier otra ciudad del planeta.

El Coliseo, el Foro Romano y el Palatino son el corazon de la Roma antigua. Caminar por el Foro imaginando la vida hace 2.000 anos es una experiencia que no deja a nadie indiferente. El Panteon, con su oculus abierto al cielo, es una obra de ingenieria que sigue asombrando a arquitectos de todo el mundo.

El Vaticano merece al menos un dia completo. Los Museos Vaticanos albergan una de las colecciones de arte mas importantes del mundo, culminando en la inigualable Capilla Sixtina con el techo de Miguel Angel. La Basilica de San Pedro y la vista desde su cupula son imprescindibles.

La gastronomia romana es de las mejores de Italia: pasta cacio e pepe, carbonara, supplì al telefono, pizza al taglio y el gelato mas cremoso del mundo. Recorrer el Trastevere de noche, con sus calles adoquinadas y restaurantes en plazas iluminadas, es la esencia de Roma.''',
        'image_url': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=800&q=80',
        'category': 'cultura',
        'emoji': '🏛️',
        'price_range': '$$',
    },
    {
        'name': 'Paris',
        'country': 'Francia',
        'description': 'La Ciudad de la Luz: arte, moda, gastronomia y el romanticismo europeo por excelencia.',
        'long_description': '''Paris es la capital de Francia y una de las ciudades mas visitadas del mundo. Conocida como la Ciudad de la Luz, combina una arquitectura haussmanniana elegante con una escena cultural y gastronomica que la convierte en referente mundial.

La Torre Eiffel es el simbolo universal de Paris y uno de los monumentos mas reconocibles del planeta. Subirla al atardecer, cuando la ciudad se ilumina gradualmente, es una experiencia magica. El Musee d'Orsay y el Louvre son dos de los museos mas importantes del mundo: el primero alberga la mayor coleccion de arte impresionista, el segundo la Mona Lisa y la Venus de Milo.

Montmartre, en lo alto de la colina del Sagrado Corazon, conserva el espiritu bohemio de la Paris del siglo XIX. Los cafes, los artistas en la Place du Tertre y las vistas de la ciudad desde la Basilica del Sacre-Coeur crean un ambiente unico.

El Marais es el barrio mas vibrante de la Paris contemporanea: galerías de arte, tiendas de diseño, el Centre Pompidou y la Plaza de los Vosgos conviven con sinagogas y pastelerias historicas. Los croissants, el boeuf bourguignon y los fromages son solo el principio de la experiencia culinaria.''',
        'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80',
        'category': 'cultura',
        'emoji': '🥐',
        'price_range': '$$$',
    },
    {
        'name': 'Buenos Aires',
        'country': 'Argentina',
        'description': 'La Paris de Sudamerica: tango, asado, arquitectura europea y una pasion por la vida inigualable.',
        'long_description': '''Buenos Aires es una de las ciudades mas vibrantes y cosmopolitas de America Latina. Con una fuerte influencia europea, especialmente italiana y española, tiene una identidad cultural unica que se expresa en su arquitectura, gastronomia, musica y arte.

San Telmo es el barrio mas historico y bohemio de la ciudad. Sus calles adoquinadas, las ferias de los domingos en la Plaza Dorrego, los bares de tango con espectaculos en vivo y las librerias de viejo crean una atmosfera incomparable. La Boca, con su colorida Caminita, es el corazon popular de la ciudad.

Palermo es el barrio mas moderno y trendy: el Barrio Japones, el Alto Palermo, los parques Tres de Febrero y el Rosedal son perfectos para descansar. La gastronomia porteña es extraordinaria: el asado argentino, las empanadas, el dulce de leche y los alfajores son parte de la identidad nacional.

El Teatro Colon es uno de los cinco mejores teatros de opera del mundo y visita obligada. El MALBA (Museo de Arte Latinoamericano) alberga una coleccion excepcional de arte del continente. Y para terminar el dia, nada mejor que cenar tarde, como hacen los porteños, y salir a bailar tango hasta el amanecer.''',
        'image_url': 'https://images.unsplash.com/photo-1589909202802-8f4aadce1849?auto=format&fit=crop&w=800&q=80',
        'category': 'cultura',
        'emoji': '💃',
        'price_range': '$',
    },
    {
        'name': 'Estambul',
        'country': 'Turquia',
        'description': 'El puente entre Oriente y Occidente: mezquitas, bazares y el Bosforo que une dos continentes.',
        'long_description': '''Estambul es la unica ciudad del mundo que se extiende sobre dos continentes, Europa y Asia, separados por el estrecho del Bosforo. Esta posicion geografica unica la convirtio durante siglos en el corazon de imperios: griego, romano, bizantino y otomano. El resultado es una ciudad de una riqueza historica y cultural incomparable.

La Mezquita Azul (Sultan Ahmed Camii) y la Hagia Sofia son los monumentos mas emblematicos. La primera, con sus seis minaretes y su interior decorado con 20.000 azulejos Iznik, es una obra maestra de la arquitectura otomana. La segunda, construida en el siglo VI como catedral cristiana y convertida en mezquita, es un simbolo de la complejidad historica de la ciudad.

El Gran Bazar, con mas de 4.000 tiendas en 61 calles cubiertas, es uno de los mercados mas grandes y antiguos del mundo. Los alfombras, especias, lamparas de mosaico y joyas son algunas de las tentaciones. El Bazar de las Especias, junto al puerto, es un festin sensorial de colores y aromas.

El desayuno turco, con sus decenas de platillos, el te en vaso de cristal y el café turco espeso son rituales matutinos que conquistan a cualquier visitante. Un crucero por el Bosforo al atardecer, viendo la ciudad iluminada desde el agua, es el cierre perfecto para un dia en Estambul.''',
        'image_url': 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=80',
        'category': 'cultura',
        'emoji': '🕌',
        'price_range': '$$',
    },
]

BLOG_POSTS = [
    {
        'title': '10 consejos para viajar por primera vez a Asia',
        'content': '''Viajar a Asia por primera vez puede ser abrumador: culturas distintas, idiomas imposibles, comidas desconocidas. Pero con la preparacion correcta, puede ser la experiencia mas transformadora de tu vida. Estos son mis 10 consejos despues de haber recorrido la region.

1. Descarga Google Translate y el paquete de idiomas offline. En muchos paises asiaticos el ingles no esta extendido, y poder comunicarte aunque sea con senias o imagenes marca la diferencia.

2. Lleva siempre efectivo. Muchos mercados, tuk-tuks y restaurantes locales no aceptan tarjeta. Cambia dinero en casas de cambio locales en lugar de aeropuertos, donde las comisiones son altisimas.

3. Respeta los codigos de vestimenta en los templos. En Japon, India, Tailandia y gran parte de Asia, los sitios sagrados exigen cubrirse hombros y rodillas. Llevar un panuelo liviano en la mochila resuelve cualquier situacion.

4. Prueba la comida callejera. Los mejores platos de Asia no estan en los restaurantes turisticos sino en los puestos de la calle. Busca donde comen los locales: si hay fila, es buena senal.

5. Contrata seguro de viaje. Los hospitales privados de calidad en Asia pueden ser muy costosos para los extranjeros sin seguro. No vale la pena arriesgar.

6. Aprende a regatear. En los mercados de Tailandia, Vietnam o Indonesia, el precio inicial es siempre negociable. Hazlo con una sonrisa y buen humor; es parte de la cultura local.

7. Sé flexible con los horarios. Los transportes pueden retrasarse, los planes pueden cambiar. Quien viaja por Asia con un itinerario rigido suele frustrarse. La improvisacion muchas veces lleva a las mejores historias.

8. Descarga mapas offline de Maps.me o Google Maps antes de llegar. El roaming puede ser caro y no siempre hay WiFi disponible.

9. Cuida lo que bebes. En muchos paises asiaticos el agua de la canilla no es potable. Compra agua embotellada o lleva una botella con filtro.

10. Abre la mente y disfruta el proceso. Asia desafía todos los esquemas. Sus colores, sonidos, olores y sabores son una explosion sensorial. Rendirse a la experiencia sin juzgarla es la clave para disfrutarla al maximo.''',
        'image_url': 'https://images.unsplash.com/photo-1464817739973-0128fe77aaa1?auto=format&fit=crop&w=800&q=80',
        'author_name': 'FlyFlask Editorial',
        'dest_name': 'Tokio',
    },
    {
        'title': 'Por que Patagonia debe estar en tu bucket list',
        'content': '''Hay lugares en el mundo que te cambian. Que te hacen sentir pequeno de una manera que no incomoda, sino que libera. La Patagonia es uno de esos lugares.

La primera vez que vi las Torres del Paine fue desde el mirador al amanecer. Habia caminado tres horas en la oscuridad, linterna en mano, para llegar antes de que saliera el sol. Cuando la primera luz toco las torres de granito y las tino de rojo y naranja, entendi por que la gente lloraba a mi lado. No era dramatismo. Era que esa imagen no cabe en el lenguaje comun.

La Patagonia es dificil. El viento puede tirarte al suelo. La lluvia puede aparecer en cinco minutos con cielo despejado. Las distancias son inmensas y los servicios escasos. Pero esa dificultad es parte del precio de admision a uno de los ultimos paisajes salvajes del planeta.

El Perito Moreno, en el lado argentino, es otro nivel. Escuchar el crujido del glaciar antes de que un bloque de hielo del tamano de un edificio se desprenda y caiga al lago con un estruendo que hace vibrar el pecho es algo que ninguna pantalla puede transmitir.

Si vas, preparate bien. Las botas de trekking son imprescindibles, al igual que capas de ropa tecnica. Reserva con anticipacion: los refugios del Circuito W se llenan con meses de anticipacion en temporada alta. Y dejate estar. La Patagonia no se ve: se vive.''',
        'image_url': 'https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&w=800&q=80',
        'author_name': 'FlyFlask Editorial',
        'dest_name': 'Patagonia',
    },
    {
        'title': 'Guia definitiva para visitar Roma en 3 dias',
        'content': '''Tres dias en Roma son pocos, pero son suficientes para enamorarse de la Ciudad Eterna para siempre. Con esta guia vas a aprovechar cada hora sin correr y sin perderte lo esencial.

DIA 1 - LA ROMA ANTIGUA
Empieza temprano en el Coliseo. Compra la entrada online con anticipacion para evitar la fila. Reserva al menos dos horas para recorrerlo bien. Luego cruza al Foro Romano y el Palatino, incluidos en la misma entrada. Almuerza en alguna trattoria del barrio y por la tarde visita el Palatino. Al caer el sol, caminata por el centro hasta la Fontana di Trevi, que de noche tiene una iluminacion magica.

DIA 2 - EL VATICANO Y TRASTEVERE
Dedica la manana entera al Vaticano. Entra a los Museos Vaticanos cuando abren (8am) para evitar las multitudes. La Capilla Sixtina puede tardar una hora en fila si vas tarde. Luego la Basilica de San Pedro y si tenes energia, sube a la cupula. Por la tarde, atraviesa el Tiber y perdete por el Trastevere. Cena ahi: es el barrio con mejor ambiente nocturno.

DIA 3 - ARTE, PLAZAS Y DOLCE VITA
El Panteon a primera hora, antes de que lleguen los grupos. Luego la Plaza Navona, el Campo de Fiori y el barrio judio. Tarde en el Borghese: los jardines son preciosos y la galeria, si reservas con anticipacion, alberga obras de Bernini y Caravaggio unicas en el mundo. Cena de despedida con una buena cacio e pepe y un tiramisu.

CONSEJOS PRACTICOS
Usa zapatos comodos: Roma se recorre a pie. El metro solo tiene dos lineas y el centro historico casi no esta cubierto. Aprende dos palabras de italiano: grazie y prego. Los romanos lo agradecen enormemente.''',
        'image_url': 'https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?auto=format&fit=crop&w=800&q=80',
        'author_name': 'FlyFlask Editorial',
        'dest_name': 'Roma',
    },
    {
        'title': 'Bali: mas alla de Instagram',
        'content': '''Todo el mundo conoce la foto del templo de Pura Ulun Danu flotando sobre el lago, o las terrazas de arroz de Tegalalang. Bali es tan fotografiada que a veces parece que ya la conoces antes de llegar. La realidad es que la isla supera siempre las expectativas.

Lo que Instagram no muestra es el olor del incienso en las ceremonias diarias que los balineses realizan al amanecer. No muestra el sonido del gamelan tocando durante horas en un templo del interior. No muestra la calidez genuina de una familia que te invita a ver una danza religiosa que no esta disenada para turistas.

Ubud es el alma de Bali. Alquila una moto (con cuidado, el transito es caotico) y explora las aldeas del interior: Penglipuran, con sus calles perfectamente ordenadas, o Sidemen, en el este, con sus vistas al Agung y sus talleres de tejido tradicional.

La costa sur, Seminyak y Canggu, son Bali pero podrian estar en cualquier ciudad trendy del mundo: buenos cafes de specialty coffee, studios de yoga a cada paso, restaurantes de comida saludable y tiendas de ropa de diseño local. Es agradable pero no es la esencia balinesa.

Para encontrar esa esencia hay que levantarse antes del amanecer para subir al Batur con un guia local y ver el sol salir sobre el volcan. O quedarse quieto en un templo mientras los sacerdotes realizan sus rituales. O simplemente conversar con el dueno del warung (restaurante local) y escuchar su vision del mundo.''',
        'image_url': 'https://images.unsplash.com/photo-1555400038-63f5ba517a47?auto=format&fit=crop&w=800&q=80',
        'author_name': 'FlyFlask Editorial',
        'dest_name': 'Bali',
    },
    {
        'title': 'Como el viaje cambio mi forma de ver el mundo',
        'content': '''Hay una frase que escuche en un hostel de Bangkok hace algunos anos: los viajes no te cambian, te revelan. En ese momento no la entendi del todo. Hoy, con muchos miles de kilometros recorridos, creo que tiene razon.

Antes de viajar tenia una imagen bastante definida de como debia ser el mundo. De como debia ser la gente. De que cosas eran normales y cuales raras. El primer viaje largo empezo a desdibujar esas certezas.

Ver como una familia en Vietnam vive con alegria genuina en una superficie que en mi pais seria considerada insuficiente para una persona. Escuchar a un taxista en Marruecos hablar con orgullo de su ciudad, de su historia, de su cultura. Compartir una comida con desconocidos en una plaza de Mexico y terminar la noche como si nos conocieramos de siempre.

Viajar enseña que hay muchas formas correctas de vivir. Que el mundo es infinitamente mas grande, mas complejo y mas hermoso de lo que cualquier escuela o pantalla puede mostrar. Que la mayoria de la gente, en todos los paises, es buena y generosa si te acercas con respeto y curiosidad.

FlyFlask nacio de esa conviccion: que registrar los viajes, compartir las experiencias y conectar con otros viajeros es una forma de mantener viva esa apertura al mundo. Cada resena, cada foto, cada destino explorado es un recordatorio de que el planeta es vasto y maravilloso, y que siempre hay algo nuevo por descubrir.''',
        'image_url': 'https://images.unsplash.com/photo-1488085061387-422e29b40080?auto=format&fit=crop&w=800&q=80',
        'author_name': 'FlyFlask Editorial',
        'dest_name': None,
    },
]


def run_seed():
    """Ejecutar dentro de un app_context activo."""
    if Destination.query.count() > 0:
        return

    print("Cargando seed de destinos y articulos...")
    dest_map = {}
    for d in DESTINATIONS:
        dest = Destination(
            name=d['name'],
            country=d['country'],
            description=d['description'],
            long_description=d['long_description'],
            image_url=d['image_url'],
            category=d['category'],
            emoji=d['emoji'],
            price_range=d['price_range'],
        )
        db.session.add(dest)
        dest_map[d['name']] = dest

    db.session.flush()

    for p in BLOG_POSTS:
        dest = dest_map.get(p['dest_name']) if p['dest_name'] else None
        post = BlogPost(
            title=p['title'],
            content=p['content'],
            image_url=p['image_url'],
            author_name=p['author_name'],
            destination_id=dest.id if dest else None,
        )
        db.session.add(post)

    db.session.commit()
    print(f"Seed listo: {len(DESTINATIONS)} destinos y {len(BLOG_POSTS)} articulos.")


if __name__ == '__main__':
    from app import app
    with app.app_context():
        run_seed()
