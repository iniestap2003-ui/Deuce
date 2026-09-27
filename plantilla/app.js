/* ===== DATOS: una caja por temporada, cargada bajo demanda ===== */
let D={partidos:[],kpi:{},ref:{},rk:null,semana:null,tipos:{}}, G={evol:{y:[],ace:[],ten:[]}};
let PROF={}, TEMP=null, ANIO=null, CUR={}, IDX=null;
const CACHE={};
async function traer(url){
 if(window.__EMB&&__EMB[url])return __EMB[url];           // vista previa: datos incrustados
 const r=await fetch(url);if(!r.ok)throw new Error(url+" "+r.status);return r.json()}
async function cargarBase(){
 const [t,r]=await Promise.all([traer("datos/temporadas.json"),traer("datos/ref.json")]);
 TEMP=t;D.ref=r.ref;G.evol=r.evol}
async function cargarTemporada(a){
 a=String(a);
 const c=CACHE[a]||(CACHE[a]=await traer(`datos/t/${a}.json`));
 let pr={};
 if(TEMP.anios[a]&&TEMP.anios[a].dp){try{pr=CACHE["p"+a]||(CACHE["p"+a]=await traer(`datos/p/${a}.json`))}catch(e){console.error("[deuce] profundo",e)}}
 ANIO=a;D.partidos=c.partidos;D.kpi=c.kpi;D.rk=c.rk;D.semana=c.semana;D.tipos=c.tipos;
 G=Object.assign({},c.G,{evol:G.evol});PROF=pr;P=D.partidos;
 document.querySelectorAll(".anio-sel").forEach(el=>el.textContent=a);
 return c}
async function traerIndice(){return IDX||(IDX=await traer("datos/indice.json"))}

const COL={"PULSO":"#FF5C39","DUELO DE SAQUES":"#4D95FF","MARCADOR ENGANOSO":"#B478FF","SIN HISTORIA":"#7A8699"};
const NOM={"PULSO":"Pulso largo","DUELO DE SAQUES":"Duelo de saques","MARCADOR ENGANOSO":"Marcador engañoso","SIN HISTORIA":"Sin historia"};
const SUPN={Clay:"Tierra",Hard:"Pista dura",Grass:"Hierba",Carpet:"Moqueta"};
const RON={F:"Final",SF:"Semifinal",QF:"Cuartos",R16:"Octavos",R32:"3ª ronda",R64:"2ª ronda",R128:"1ª ronda",RR:"Grupos",BR:"Bronce"};
const E=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[<>&"]/g,c=>({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"}[c]));
const fF=s=>{const[a,b,c]=s.split("-");return `${c}/${b}/${a}`};
const pc=v=>v==null?"—":Math.round(v*100)+"%";
const cssv=n=>getComputedStyle(document.body).getPropertyValue(n).trim();
let P=[],V=[],tipos=new Set(),soloRobo=false,soloDeep=false,tope=50;
const MET=[
{k:"disputa",n:"Disputa",p:1,c:"#1FD68A",q:"Cuánto se peleó cada juego por dentro.",
 ico:'<circle cx="20" cy="20" r="15" stroke="currentColor" stroke-width="2.2"/><path d="M20 5v30M5 20h30" stroke="currentColor" stroke-width="1.1" opacity=".45"/>',
 t:"El marcador solo guarda quién ganó cada juego, no lo que costó ganarlo. Un 6-0 puede ser seis juegos regalados o seis juegos que se fueron a deuce una y otra vez. Sobre el papel son idénticos. En la pista no tienen nada que ver.",
 como:"Un juego ganado sin conceder un punto se resuelve en cuatro puntos. Si llega a deuce ya hacen falta seis, y cada empate añade dos más. Así que basta con dividir todos los puntos del partido entre todos los juegos para saber cuánto costó el juego medio. Si sale cerca de cuatro, fue un paseo. Si sale por encima de siete, cada juego fue una batalla. Ese número se estira después a una escala de cero a cien para que se lea de un vistazo.",
 e:"Murray ganó 6-0 6-0 a Kendrick y aun así tuvo que jugar 107 puntos y salvar tres bolas de break. El resultado dice paseo. La disputa dice lo contrario.",
 esc:[0,100,46.7],escT:"0 = juegos resueltos sin esfuerzo · 100 = cada juego al límite"},

{k:"tension",n:"Tensión",p:1,c:"#FF5C39",q:"Lo cerca que estuvo de caer del otro lado.",
 ico:'<path d="M4 31L12 14l8 10 8-16 8 11" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>',
 t:"No es lo mismo ganar 7-5 que ganar 6-1, aunque los dos sean un set. La tensión mide cuánto le faltó al perdedor para llevarse cada parcela del partido, y con eso resume si el resultado estuvo en el aire o nunca lo estuvo.",
 como:"Se mira set por set la distancia entre los dos marcadores. Cuanto más pegados, más aporta ese set. Un 7-6 vale casi el máximo, un 6-4 bastante, un 6-0 no aporta nada. Después se promedian todos los sets del partido. Y si el encuentro llegó hasta el último set posible se le añade una prima, porque eso significa que todo se decidió a cara o cruz.",
 e:"Alcaraz y Sinner en Roland Garros 2025 marcaron 88. Solo dos de cada cien partidos de ese año apretaron más.",
 av:"Mide igualdad, no calidad. Dos jugadores fallando a la vez también producen marcadores pegados.",
 esc:[0,100,58.3],escT:"0 = nunca hubo partido · 100 = todo al límite"},

{k:"robo",n:"Robo",p:1,c:"#B478FF",q:"Ganar habiendo hecho menos puntos que el rival.",
 ico:'<path d="M7 20h26M25 11l8 9-8 9" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>',
 t:"Parece un error de cálculo y ocurre en uno de cada veinte partidos. El tenis no reparte el premio a quien más puntos suma, sino a quien los suma en el momento correcto. Perder un set 6-0 cuesta exactamente lo mismo que perderlo 7-6, así que se pueden regalar puntos a manos llenas sin pagar ningún precio por ello.",
 como:"Se suman todos los puntos que ganó cada jugador a lo largo del encuentro, los que hizo sacando y los que le arrancó al saque del contrario. Si el que levantó los brazos al final resulta que sumó menos de la mitad, ahí hay un robo.",
 e:"Final de Wimbledon 2019. Djokovic se lleva el trofeo con 204 puntos. Federer acabó con 218.",
 av:"No es ningún demérito para el ganador. Casi siempre significa que fue quien no tembló cuando tocaba."},

{k:"dominacion",n:"Control",p:1,c:"#3D7BFF",q:"Quién mandaba de verdad ahí dentro.",
 ico:'<rect x="6" y="23" width="7" height="12" fill="currentColor" opacity=".4"/><rect x="16" y="14" width="7" height="21" fill="currentColor" opacity=".7"/><rect x="26" y="5" width="7" height="30" fill="currentColor"/>',
 t:"Un solo número para resumir quién llevó la iniciativa. Contar aces engaña, porque un jugador puede sacar de maravilla y estar perdiendo. Esto compara lo que le arrancas al rival con lo que él te arranca a ti, que es lo que realmente decide un partido de tenis.",
 como:"Por un lado se mira qué proporción de puntos consigues cuando saca el otro, que es lo difícil. Por otro, qué proporción le concedes tú cuando sacas, que es lo que no deberías estar cediendo. Si lo primero es mayor que lo segundo, llevabas tú la iniciativa. Si es menor, era suya. El uno es la frontera exacta entre las dos cosas.",
 e:"En aquella final de Wimbledon el número dijo lo que las estadísticas oficiales callaron: Federer dominó, Djokovic ganó.",
 esc:[0,3,1.32],escT:"por debajo de 1 la llevaba el rival · por encima, mandabas tú"},

{k:"espectaculo",n:"Espectáculo",p:1,c:"#FFB74D",q:"Si merecía la pena quedarse despierto.",
 ico:'<path d="M20 4l4.6 10.2L36 15.8l-8 7.7 1.9 11.1L20 29.3 10.1 34.6 12 23.5l-8-7.7 11.4-1.6z" fill="currentColor"/>',
 t:"Un partido memorable necesita dos cosas a la vez: que estuviera reñido y que hubiera algo en juego. Una primera ronda igualadísima en un torneo menor es entretenida, pero no se recuerda. Una final de Grand Slam que se va al quinto set no se olvida nunca.",
 como:"Primero se pesa cuánto había en juego, combinando la categoría del torneo con lo avanzada que estaba la ronda. Un Grand Slam pesa el doble que un torneo normal, y una final pesa el triple que una primera ronda. Después ese peso se multiplica por lo reñido que estuvo el encuentro. Solo cuando las dos cosas son altas sale un número alto.",
 e:"La final de Roland Garros 2025 entre Alcaraz y Sinner encabeza la lista histórica.",
 esc:[0,12,3.4],escT:"0 = trámite · 12 = final de Grand Slam al límite"},

{k:"volatilidad",n:"Volatilidad",p:1,c:"#B478FF",q:"Si alguien se descompuso y volvió.",
 ico:'<path d="M4 20c6-15 10 15 16 0s10-15 16 0" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round"/>',
 t:"Dos partidos pueden acabar con la misma diferencia y no parecerse en nada. Un 6-4 6-4 es un pulso firme de principio a fin. Un 6-1 1-6 6-1 es un ataque de nervios con final feliz. El resultado no distingue entre los dos; esto sí.",
 como:"Se observa cómo de desigual fue cada set y se comprueba si todos se parecieron entre sí o no. Cuando los sets tienen marcadores similares, el partido fue estable. Cuando hay un set muy desequilibrado hacia un lado y otro muy desequilibrado hacia el otro, el encuentro fue una montaña rusa y el número sube.",
 esc:[0,6,1.25],escT:"0 = pulso firme · 6 = montaña rusa"},

{k:"sorpresa",n:"Sorpresa",p:1,c:"#FF5C39",q:"Cuánto se rompió el guion.",
 ico:'<path d="M20 4l3 12h13l-10.5 7.6L29.5 36 20 28.4 10.5 36l4-12.4L4 16h13z" stroke="currentColor" stroke-width="2.1" fill="none" stroke-linejoin="round"/>',
 t:"Decir que ganó el peor clasificado no significa nada por sí solo. Que el número sesenta gane al cincuenta pasa todas las semanas y no lo recuerda nadie. Que el ciento setenta y cinco tumbe al número uno del mundo se cuenta durante años.",
 como:"Se compara la distancia entre los puestos de los dos jugadores, pero no restando sino dividiendo. Eso hace que subir diez puestos desde el fondo de la clasificación pese mucho menos que ganarle a alguien que está diez veces por delante de ti. Así el número refleja lo improbable que era el resultado, no la distancia aritmética.",
 e:"Kokkinakis, ciento setenta y cinco del mundo, ganó a Federer en Miami 2018. Nadie ha roto tanto el guion desde entonces.",
 esc:[0,5,0],escT:"0 = ganó el favorito · 5 = esto no debería haber pasado"},

{k:"desperdicio",n:"Desperdicio",p:1,c:"#FFB74D",q:"Las oportunidades que tiró a la basura.",
 ico:'<circle cx="20" cy="20" r="14" stroke="currentColor" stroke-width="2.2" fill="none"/><path d="M13.5 13.5l13 13M26.5 13.5l-13 13" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>',
 t:"Una bola de break es la puerta abierta: el punto que te permite quitarle el saque al rival y romper el partido. Cerrarla una vez tras otra es la forma más cruel de perder, y a veces de ganar sudando el triple de lo necesario.",
 como:"Se cuentan todas las veces que un jugador se puso a un punto de romper el servicio del contrario, y se resta cuántas de esas veces lo consiguió de verdad. Lo que queda son las ocasiones que tuvo delante y dejó escapar.",
 e:"Fucsovics falló veintisiete contra Dimitrov. Veintisiete. Y aun así ganó el partido."},

{k:"asimetria",n:"Asimetría",p:1,c:"#1FD68A",q:"Si ganó con el brazo o con las piernas.",
 ico:'<path d="M20 5v30M20 5l-9 9M20 5l9 9M20 35l-9-9M20 35l9-9" stroke="currentColor" stroke-width="2.1" fill="none" stroke-linecap="round"/>',
 t:"Hay dos maneras de ganar un partido de tenis. Una es imponerse desde el saque, golpeando primero y sin dar opción. La otra es devolver todo lo que llega hasta que el de enfrente se rompe. Casi nadie hace las dos cosas igual de bien, y eso retrata a un jugador mejor que cualquier etiqueta.",
 como:"Se mide cuánto destacó sacando por encima de lo que hace un jugador corriente del circuito, y cuánto destacó restando por encima de ese mismo listón. Después se comparan las dos cosas entre sí. Ojo a un detalle importante: no compara los puntos que gana sacando con los que gana restando, porque sacar da ventaja siempre y entonces todo el mundo saldría positivo. Compara lo mucho o poco que destaca en cada faceta. El cero significa que destacó igual en las dos. Positivo, que su saque sobresale más de lo que sobresale su resto.",
 e:"En un extremo están Karlović, Isner y Raonic, que viven del saque. En el otro, Schwartzman, que vive de devolverlo todo."},

{k:"escape",n:"Bolas de break salvadas de más",p:1,c:"#FF5C39",q:"Cuántas salvó por encima de lo esperable.",
 ico:'<path d="M20 5l13 6v11c0 8-5.5 13-13 15-7.5-2-13-7-13-15V11z" stroke="currentColor" stroke-width="2.1" fill="none"/>',
 t:"Salvar dos bolas de break de dos suena impecable, pero puede ser casualidad. Salvar nueve de quince, con esa presión encima durante todo el partido, es otra cosa muy distinta. El porcentaje a secas no distingue entre ambas situaciones.",
 como:"En el circuito se salvan alrededor de seis de cada diez bolas de break. Sabiendo cuántas afrontó un jugador se puede calcular cuántas debería haber salvado rindiendo como cualquier otro, y compararlo con las que salvó de verdad. El resultado es un número de bolas: un dos significa que salvó dos más de las que le tocaban; un menos uno, que se dejó una por el camino.",
 e:"Es la diferencia entre un portero que para tres tiros fáciles y otro que para dos imposibles."},

{k:"ptssaque",n:"Puntos ganados al saque",p:0,c:"#3D7BFF",q:"Qué pasa cuando le toca servir.",
 ico:'<path d="M20 35V9M20 9l-7 7M20 9l7 7" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round"/><circle cx="20" cy="35" r="3" fill="currentColor"/>',
 t:"Seguramente la cifra que mejor anticipa quién va a ganar un partido. En el tenis masculino quien saca parte con ventaja en cada punto, así que sostener el propio servicio es la obligación básica. El que deja de cumplirla, pierde.",
 como:"De todos los puntos en los que un jugador puso la pelota en juego con su saque, se mira cuántos acabó llevándose, sumando los que ganó con el primer servicio y los que ganó con el segundo.",
 esc:[.5,.9,.69],escT:"por debajo del 61% flojea · por encima del 78% es intocable"},

{k:"primeros",n:"Primeros saques dentro",p:0,c:"#3D7BFF",q:"Cuántos primeros servicios entran.",
 ico:'<rect x="6" y="6" width="28" height="28" rx="4" stroke="currentColor" stroke-width="2.1" fill="none"/><path d="M13 20l5 5 9-10" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round"/>',
 t:"Un clásico que engaña a mucha gente. Meter muchísimos primeros saques no sirve de nada si se sacan a media potencia para no fallar. Solo significa algo leído junto al porcentaje de puntos que se ganan con ellos.",
 como:"De todas las veces que un jugador sacó, cuántas veces su primer intento cayó dentro del cuadro sin necesidad de recurrir al segundo servicio.",
 esc:[.4,.85,.626],escT:"la media del circuito ronda el 63%"},

{k:"eficiencia",n:"Eficiencia",p:1,c:"#1FD68A",q:"Si aprovechó sus puntos o los malgastó.",
 ico:'<path d="M6 30l8-8 6 6 14-16" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="34" cy="12" r="3" fill="currentColor"/>',
 t:"En tenis no ganan los puntos, ganan los juegos. Y los puntos no valen todos lo mismo: el que decide un juego vale muchísimo más que el cuarto punto de un juego que ya llevas ganado. Hay jugadores que acumulan puntos donde no sirven de nada y los echan en falta donde importan.",
 como:"Se compara qué porcentaje de los juegos se llevó un jugador con qué porcentaje de los puntos ganó. Si se quedó con el sesenta por ciento de los juegos habiendo ganado solo el cincuenta y dos por ciento de los puntos, significa que los colocó donde hacían falta y la cifra sale positiva. Si ocurre al revés, es que ganó muchos puntos en juegos que ya tenía resueltos o que ya estaban perdidos, y sale negativa.",
 e:"Es la diferencia entre el que gana un juego a cero y luego pierde tres seguidos por poco, y el que va justo en todos pero se lleva los que cuentan.",
 av:"Está muy relacionada con el robo: casi todos los partidos ganados con menos puntos que el rival tienen una eficiencia alta."}];

/* ===== PISTA DE FONDO + PELOTA ===== */
function pista(){
 const svg=`<svg id="court" viewBox="0 0 1097 2377" preserveAspectRatio="xMidYMid slice"
  style="position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:.13">
  <g fill="none" stroke="currentColor" stroke-width="7" vector-effect="non-scaling-stroke">
   <rect x="4" y="4" width="1089" height="2369"/>
   <line x1="137" y1="4" x2="137" y2="2373"/><line x1="960" y1="4" x2="960" y2="2373"/>
   <line x1="137" y1="548" x2="960" y2="548"/><line x1="137" y1="1829" x2="960" y2="1829"/>
   <line x1="548" y1="548" x2="548" y2="1829"/>
   <line x1="4" y1="1188" x2="1093" y2="1188" stroke-width="11"/>
  </g></svg>`;
 document.body.insertAdjacentHTML("afterbegin",svg);
 const c=document.createElement("canvas");
 c.id="rally";c.style.cssText="position:fixed;inset:0;width:100%;height:100%;z-index:0;pointer-events:none";
 document.body.insertBefore(c,document.body.firstChild.nextSibling);
 const x=c.getContext("2d"),dpr=Math.min(devicePixelRatio||1,2);
 let W,H;
 function size(){W=innerWidth;H=innerHeight;c.width=W*dpr;c.height=H*dpr;x.setTransform(dpr,0,0,dpr,0,0)}
 size();

 // La pelota SALE por un borde y el golpe de vuelta ENTRA POR ESE MISMO PUNTO.
 // Así la trayectoria es coherente: el jugador está justo detrás de donde salió.
 let b=null, ultimaX=null, desde="arriba", ang=0;
 function golpe(){
  const fuera=H*.62;                         // cuánto vuela por detrás del borde
  const entra = desde==="arriba" ? -fuera : H+fuera;
  const sale  = desde==="arriba" ? H+fuera : -fuera;
  // el punto de entrada es donde salió la vez anterior (el jugador la devuelve ahí)
  const x0 = ultimaX==null ? W*(.3+Math.random()*.4) : ultimaX;
  // hacia dónde la manda: cruzado, paralelo o al centro
  const jugada=Math.random();
  const x1 = jugada<.45 ? W-x0 + (Math.random()-.5)*W*.12      // cruzado
           : jugada<.78 ? x0 + (Math.random()-.5)*W*.18        // paralelo
           : W*.5 + (Math.random()-.5)*W*.14;                  // al centro
  const plano = Math.random()<.42;
  const T = plano ? 78+Math.random()*26 : 126+Math.random()*54;
  b={x0,x1:Math.max(W*.06,Math.min(W*.94,x1)),y0:entra,y1:sale,T,t:0,
     arco: plano ? 26+Math.random()*30 : 72+Math.random()*80,
     r: 10+Math.random()*2, giro: (plano?1.9:1.15)*(Math.random()<.5?-1:1)};
 }
 golpe();

 (function loop(){
  x.clearRect(0,0,W,H);
  if(b){
   b.t++;
   const p=b.t/b.T;
   if(p>=1){
    ultimaX=b.x1; desde = desde==="arriba"?"abajo":"arriba";
    b=null; setTimeout(golpe, 140+Math.random()*420);   // el jugador prepara el golpe
   }else{
    const q=p*(1.05-0.05*p);
    const px=b.x0+(b.x1-b.x0)*q;
    const py=b.y0+(b.y1-b.y0)*q-Math.sin(p*Math.PI)*b.arco;
    const rr=b.r*(1+.26*Math.sin(p*Math.PI));
    ang+=b.giro*.055;
    // sombra sobre la pista
    x.globalAlpha=.11;x.fillStyle="#000";
    x.beginPath();x.ellipse(px+rr*.45,py+rr*1.8,rr*.9,rr*.28,0,0,7);x.fill();
    // pelota, rotando sobre sí misma
    x.save();x.translate(px,py);x.rotate(ang);
    const g=x.createRadialGradient(-rr*.34,-rr*.38,rr*.12,0,0,rr);
    g.addColorStop(0,"#F4FF8C");g.addColorStop(.5,"#D6F52B");g.addColorStop(1,"#93B310");
    x.globalAlpha=.95;x.fillStyle=g;x.beginPath();x.arc(0,0,rr,0,7);x.fill();
    // las dos costuras curvas, que es lo que delata el giro
    x.globalAlpha=.82;x.strokeStyle="#FCFFE8";x.lineWidth=rr*.15;x.lineCap="round";
    x.beginPath();x.arc(-rr*1.02,0,rr*1.28,-0.72,0.72);x.stroke();
    x.beginPath();x.arc(rr*1.02,0,rr*1.28,Math.PI-0.72,Math.PI+0.72);x.stroke();
    x.restore();x.globalAlpha=1;
   }
  }
  requestAnimationFrame(loop)})();
 let t;addEventListener("resize",()=>{clearTimeout(t);t=setTimeout(size,250)});
}


/* ===== MAPA DE ESTILOS ===== */
let MAPV=0;
function mapaEstilos(){const miV=++MAPV;
 const box=E("swarm"),c=E("sw");if(!box||!c)return;
 const D2=G.estilos||[];if(!D2.length)return;
 const x=c.getContext("2d"),dpr=Math.min(devicePixelRatio||1,2);
 let W,H,N=[],hov=null,run=false;
 let tip=box.querySelector(".mtip");
 if(!tip){tip=document.createElement("div");tip.className="mtip";box.appendChild(tip)}
 const sv=D2.map(d=>d.sv),re_=D2.map(d=>d.re);
 const sMin=Math.min(...sv)-.6,sMax=Math.max(...sv)+.6,rMin=Math.min(...re_)-.6,rMax=Math.max(...re_)+.6;
 const pMax=Math.max(...D2.map(d=>d.p));
 const M={l:64,r:30,t:34,b:52};
 function size(){const r=box.getBoundingClientRect();W=r.width;H=r.height;
  c.width=W*dpr;c.height=H*dpr;x.setTransform(dpr,0,0,dpr,0,0);
  N=D2.map(d=>({...d,
   px:M.l+(W-M.l-M.r)*(d.sv-sMin)/(sMax-sMin),
   py:H-M.b-(H-M.t-M.b)*(d.re-rMin)/(rMax-rMin),
   r:3.2+6.5*Math.sqrt(d.p/pMax)}));
  N.sort((a,b)=>a.p-b.p)}
 size();
 box.onpointermove=e=>{const r=box.getBoundingClientRect();
  const mx=e.clientX-r.left,my=e.clientY-r.top;
  let b=null,bd=1e9;
  N.forEach(n=>{const d=(n.px-mx)**2+(n.py-my)**2;if(d<bd){bd=d;b=n}});
  hov=bd<900?b:null;
  if(hov){tip.classList.add("on");
   tip.innerHTML=`<b>${esc(hov.full)}</b>
    <span>${hov.p} partidos esta temporada</span>
    <i>${hov.sv>0?"+":""}${hov.sv} puntos al saque sobre la media de su superficie</i>
    <i>${hov.re>0?"+":""}${hov.re} puntos al resto sobre esa misma media</i>`;
   const tw=Math.min(270,W-24);tip.style.width=tw+"px";
   tip.style.left=Math.max(8,Math.min(W-tw-8,hov.px-tw/2))+"px";
   tip.style.top=(hov.py>H/2?hov.py-tip.offsetHeight-16:hov.py+18)+"px";
  } else tip.classList.remove("on")};
 box.onpointerleave=()=>{hov=null;tip.classList.remove("on")};
 function frame(){
  if(!run||miV!==MAPV)return;
  const ln=cssv("--line"),mu=cssv("--muted"),acc=cssv("--acc"),ink=cssv("--ink");
  x.clearRect(0,0,W,H);
  const cx0=M.l+(W-M.l-M.r)*(0-sMin)/(sMax-sMin);
  const cy0=H-M.b-(H-M.t-M.b)*(0-rMin)/(rMax-rMin);
  // ejes en cero = jugador corriente
  x.strokeStyle=ln;x.lineWidth=1;x.setLineDash([5,6]);
  x.beginPath();x.moveTo(cx0,M.t);x.lineTo(cx0,H-M.b);x.moveTo(M.l,cy0);x.lineTo(W-M.r,cy0);x.stroke();x.setLineDash([]);
  x.font="600 10.5px Sora";x.fillStyle=mu;x.globalAlpha=.85;
  x.textAlign="center";x.fillText("media del circuito",cx0,M.t-12);
  x.textAlign="right";x.fillText("media",M.l-8,cy0+3);
  // etiquetas de cuadrante
  x.font="700 11px Sora";x.globalAlpha=.55;
  x.textAlign="right";x.fillText("RESTADOR",W-M.r-4,M.t+2);
  x.textAlign="left";x.fillText("COMPLETO",M.l+4,M.t+2);
  x.textAlign="left";x.fillText("EN APUROS",M.l+4,H-M.b+16);
  x.textAlign="right";x.fillText("SACADOR",W-M.r-4,H-M.b+16);
  x.globalAlpha=1;
  // titulos de eje
  x.font="500 11.5px Sora";x.fillStyle=mu;x.textAlign="center";
  x.fillText("gana más con su saque  →",W/2,H-14);
  x.save();x.translate(18,H/2);x.rotate(-Math.PI/2);x.fillText("gana más restando  →",0,0);x.restore();
  // puntos
  N.forEach(n=>{
   const es=n===hov, grande=n.p>=pMax*.52;
   x.globalAlpha=es?1:.5;
   x.fillStyle=es?acc:mu;
   x.beginPath();x.arc(n.px,n.py,es?n.r+2.5:n.r,0,7);x.fill();
   if(es){x.globalAlpha=.3;x.strokeStyle=acc;x.lineWidth=1.5;
    x.beginPath();x.arc(n.px,n.py,n.r+10,0,7);x.stroke()}
   if(grande&&!es){x.globalAlpha=.78;x.fillStyle=ink;x.font="600 11px Sora";
    x.textAlign="center";x.textBaseline="bottom";x.fillText(n.n,n.px,n.py-n.r-5)}
   if(es){x.globalAlpha=1;x.fillStyle=ink;x.font="700 13px Sora";
    x.textAlign="center";x.textBaseline="bottom";x.fillText(n.n,n.px,n.py-n.r-8)}
  });
  x.globalAlpha=1;requestAnimationFrame(frame)}
 new IntersectionObserver(es=>es.forEach(e=>{
  if(e.isIntersecting&&!run){run=true;frame()}else if(!e.isIntersecting)run=false}),{threshold:.06}).observe(box);
 let t;addEventListener("resize",()=>{clearTimeout(t);t=setTimeout(size,220)});
}

/* ===== barras en proporcion ===== */
function barrasPct(id,labels,cols,pct,h){
 if(!pct){barras(id,labels,cols.map((c,ci)=>({c:COL[c],v:G.tipo_sup.v.map(r=>r[ci])})),h);return}
 const o=cx(id,h);if(!o)return;const{x,W,H}=o;
 const bh=(H-34)/labels.length;
 labels.forEach((L,i)=>{
  let px=74;const y=8+i*bh;
  cols.forEach((c,j)=>{
   const w=(W-84)*pct[i][j]/100;
   x.fillStyle=COL[c];x.globalAlpha=.88;
   x.beginPath();x.roundRect(px,y,Math.max(0,w-1.5),bh-16,3);x.fill();
   if(w>36){x.globalAlpha=1;x.fillStyle="#08090C";x.font="700 10px Sora,sans-serif";x.textAlign="center";
    x.textBaseline="middle";x.fillText(pct[i][j]+"%",px+w/2,y+(bh-16)/2)}
   px+=w});
  x.globalAlpha=1;x.fillStyle=cssv("--ink");x.font="600 12px Sora,sans-serif";
  x.textAlign="right";x.textBaseline="middle";x.fillText(L,66,y+(bh-16)/2)});
 // leyenda
 x.font="400 10px Sora,sans-serif";x.textBaseline="middle";x.textAlign="left";
 let lx=74;cols.forEach(c=>{x.fillStyle=COL[c];x.beginPath();x.arc(lx+4,H-12,4,0,7);x.fill();
  x.fillStyle=cssv("--muted");x.fillText(NOM[c],lx+12,H-12);lx+=x.measureText(NOM[c]).width+36});
}


/* ---------- tarjetas de medida ---------- */
function cards(){
 E("mgrid").innerHTML=MET.map((m,i)=>`<button class="mcard rv" style="--c:${m.c}" data-m="${i}">
  <svg viewBox="0 0 40 40" fill="none">${m.ico}</svg>
  <div class="n">${m.n}</div><p>${m.q}</p><div class="go">ver cómo se calcula</div></button>`).join("");
 document.querySelectorAll("[data-m]").forEach(b=>{
  b.onclick=()=>abrirM(+b.dataset.m);
  b.onpointermove=e=>{const r=b.getBoundingClientRect();
   b.style.setProperty("--mx",(e.clientX-r.left)+"px");b.style.setProperty("--my",(e.clientY-r.top)+"px")};
 });
}
function abrirM(i){
 const m=MET[i];
 E("mT").innerHTML=`<svg viewBox="0 0 40 40" fill="none" style="width:44px;height:44px;color:${m.c}">${m.ico}</svg>
  <h2 style="font-size:clamp(28px,5vw,42px);margin:12px 0 8px">${m.n}</h2>
  <p style="color:var(--muted);margin:0;font-size:17px">${m.q}</p>
  `;
 let es="";
 if(m.esc){const[a,b,med]=m.esc,p=100*(med-a)/(b-a);
  es=`<div style="margin:26px 0 8px">
   <div style="font-size:13px;color:var(--muted);margin-bottom:10px">${m.escT||""}</div>
   <div class="eb" style="height:10px"><i style="width:100%;background:linear-gradient(90deg,var(--surf),${m.c})"></i><u style="left:${p}%;height:18px;top:-4px"></u></div>
   <div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--muted);margin-top:8px">
    <span>${a}</span><span>la marca es el partido corriente</span><span>${b}</span></div></div>`}
 E("mB").innerHTML=`
  <p style="font-size:16.5px;line-height:1.62">${m.t}</p>
  <div style="margin:28px 0 0;padding:24px;border:1px solid var(--line);border-radius:18px;background:var(--surf)">
   <div style="font-family:var(--sans);font-weight:600;font-size:12px;color:${m.c};margin-bottom:12px">cómo se obtiene</div>
   <p style="margin:0;font-size:15.5px;line-height:1.62;color:var(--ink)">${m.como}</p>
  </div>
  ${es}
  ${m.e?`<div class="ejem" style="--c:${m.c}"><strong>Un caso real.</strong> ${m.e}</div>`:""}
  ${m.av?`<div class="avis"><strong style="color:var(--ink)">Lo que hay que saber.</strong> ${m.av}</div>`:""}`;
 E("dM").showModal();
}


/* ---------- canvas ---------- */
function cx(id,h){const c=E(id);if(!c)return null;const r=c.getBoundingClientRect();
 if(!r.width)return null;const d=Math.min(devicePixelRatio||1,2);
 c.width=r.width*d;c.height=h*d;c.style.height=h+"px";const x=c.getContext("2d");x.scale(d,d);return{x,W:r.width,H:h}}
function barras(id,labels,series,h){const o=cx(id,h);if(!o)return;const{x,W,H}=o;
 const bw=(W-8)/labels.length,max=Math.max(...series.flatMap(s=>s.v))*1.12||1;
 labels.forEach((L,i)=>{let y=H-24;
  series.forEach(s=>{const hh=(H-42)*s.v[i]/max;x.fillStyle=s.c;
   const bx=4+i*bw+bw*.17,bwd=bw*.66;
   x.beginPath();x.roundRect(bx,y-hh,bwd,hh,[4,4,0,0]);x.fill();y-=hh});
  x.fillStyle=cssv("--muted");x.font="10px 'Space Mono',monospace";x.textAlign="center";x.fillText(L,4+i*bw+bw*.5,H-8)})}
function hist(id,v,e,col,h){const o=cx(id,h);if(!o)return;const{x,W,H}=o;
 const bw=W/v.length,max=Math.max(...v)||1;
 v.forEach((n,i)=>{const hh=(H-30)*n/max;const g=x.createLinearGradient(0,H-hh,0,H);
  g.addColorStop(0,col);g.addColorStop(1,col+"18");x.fillStyle=g;
  x.beginPath();x.roundRect(i*bw+1.5,H-24-hh,bw-3,hh,[3,3,0,0]);x.fill()});
 x.fillStyle=cssv("--muted");x.font="10px 'Space Mono',monospace";x.textAlign="left";x.fillText(Math.round(e[0]),2,H-7);
 x.textAlign="right";x.fillText(Math.round(e[e.length-1]),W-2,H-7)}
function linea(id,xs,ys,col,h){const o=cx(id,h);if(!o)return;const{x,W,H}=o,pad=36;
 const mn=Math.min(...ys)*.96,mx=Math.max(...ys)*1.05;
 const px=i=>pad+(W-pad-10)*i/(xs.length-1),py=v=>H-28-(H-50)*(v-mn)/(mx-mn);
 x.strokeStyle=cssv("--line");x.lineWidth=1;
 [0,.5,1].forEach(f=>{const y=py(mn+(mx-mn)*f);x.beginPath();x.moveTo(pad,y);x.lineTo(W-10,y);x.stroke();
  x.fillStyle=cssv("--muted");x.font="10px 'Space Mono',monospace";x.textAlign="right";x.fillText((mn+(mx-mn)*f).toFixed(1),pad-6,y+3)});
 const g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,col+"44");g.addColorStop(1,col+"00");
 x.beginPath();ys.forEach((v,i)=>i?x.lineTo(px(i),py(v)):x.moveTo(px(i),py(v)));
 x.lineTo(px(ys.length-1),H-28);x.lineTo(px(0),H-28);x.closePath();x.fillStyle=g;x.fill();
 x.beginPath();ys.forEach((v,i)=>i?x.lineTo(px(i),py(v)):x.moveTo(px(i),py(v)));
 x.strokeStyle=col;x.lineWidth=2.4;x.lineJoin="round";x.stroke();
 x.fillStyle=col;ys.forEach((v,i)=>{if(i%8===0||i===ys.length-1){x.beginPath();x.arc(px(i),py(v),3,0,7);x.fill()}});
 x.fillStyle=cssv("--muted");x.font="10px 'Space Mono',monospace";x.textAlign="center";
 [0,Math.floor(xs.length/2),xs.length-1].forEach(i=>x.fillText(xs[i],px(i),H-9))}
function nube(){const mx=Math.max(...G.nube.map(d=>d.v)),mn=Math.min(...G.nube.map(d=>d.v));
 E("nube").innerHTML=G.nube.map(d=>{const s=14+27*(d.v-mn)/(mx-mn||1);
  const t=Math.max(0,Math.min(1,(d.t-50)/18));
  const c=`hsl(${215-195*t},${45+30*t}%,${52-6*t}%)`;
  return `<span style="font-size:${s.toFixed(1)}px;color:${c}" title="${esc(d.n)} · ${d.v} partidos · tensión media ${d.t}">${esc(d.n)}</span>`}).join("")}
let pts=[];
function plano(){const box=E("plano"),c=E("cv"),r=box.getBoundingClientRect();
 if(!r.width)return;const dp=Math.min(devicePixelRatio||1,2);
 c.width=r.width*dp;c.height=r.height*dp;const x=c.getContext("2d");x.scale(dp,dp);
 const W=r.width,H=r.height,ln=cssv("--line");
 const t0=performance.now();
 (function paso(){const k=Math.min(1,(performance.now()-t0)/1000),e=1-Math.pow(1-k,3);
  x.clearRect(0,0,W,H);
  x.strokeStyle=ln;x.setLineDash([5,6]);x.lineWidth=1.2;x.beginPath();
  x.moveTo(W*.583,0);x.lineTo(W*.583,H);x.moveTo(0,H-H*.467);x.lineTo(W,H-H*.467);x.stroke();x.setLineDash([]);
  pts=[];
  P.forEach((p,i)=>{if(p.te==null||p.di==null||i/P.length>e)return;
   const ppx=W*p.te/100,ppy=H-H*p.di/100,rad=1.6+(p.im||1)*.42;
   x.globalAlpha=.55;x.fillStyle=COL[p.tp]||"#7A8699";
   x.beginPath();x.arc(ppx,ppy,rad,0,7);x.fill();pts.push({px:ppx,py:ppy,p})});
  x.globalAlpha=1;if(k<1)requestAnimationFrame(paso)})()}

/* ---------- analisis ---------- */
let todas=false;
function filtrar(){const q=E("q").value.toLowerCase().trim(),s=E("fs").value,t=E("ft").value,r=E("fr").value,o=E("fo").value;
 if(todas){buscarTodas(q);return}
 V=P.filter(p=>{if(s&&p.s!==s)return false;if(t&&p.t!==t)return false;if(r&&p.r!==r)return false;
  if(tipos.size&&!tipos.has(p.tp))return false;if(soloRobo&&!p.rb)return false;if(soloDeep&&!p.dp)return false;
  if(q&&!(p.w.toLowerCase().includes(q)||p.l.toLowerCase().includes(q)||p.t.toLowerCase().includes(q)))return false;
  return true});
 V.sort((a,b)=>{const A=a[o],B=b[o];if(A==null)return 1;if(B==null)return -1;return A<B?1:A>B?-1:0});
 tope=50;pintar()}
function pintar(){E("cuenta").textContent=V.length+" partidos";E("vacio").hidden=V.length>0;
 E("lista").innerHTML=V.slice(0,tope).map(p=>`<button class="pit${p.dp?" dp":""}" data-i="${P.indexOf(p)}">
  <div class="f">${fF(p.d)}</div>
  <div><div class="j"><b>${esc(p.w)}</b> <span>venció a</span> ${esc(p.l)}</div>
   <div class="mt">${esc(p.sc)} · ${esc(p.t)} · ${RON[p.r]||p.r}${p.mi?" · "+p.mi+" min":""}</div></div>
  <div class="der">${p.dp?'<span class="sello-dp">★ ANÁLISIS PROFUNDO</span>':""}<span class="tg2" style="color:${COL[p.tp]}">${NOM[p.tp]}</span>
   ${p.rb?'<span class="tg2" style="color:#B478FF">robo</span>':""}
   <span class="f">tensión ${p.te??"—"} · disputa ${p.di??"—"}</span></div></button>`).join("");
 E("mas").hidden=V.length<=tope;
 document.querySelectorAll(".pit").forEach(b=>b.onclick=()=>abrirP(+b.dataset.i))}
async function buscarTodas(q){
 const L=E("lista");
 if(q.length<3){V=[];E("cuenta").textContent="escribe al menos tres letras para buscar en las 36 temporadas";
  L.innerHTML="";E("vacio").hidden=true;E("mas").hidden=true;return}
 E("cuenta").textContent="buscando…";
 let X;try{X=await traerIndice()}catch(e){E("cuenta").textContent="el índice no está disponible en esta versión";return}
 const jm=X.j.map(n=>n.toLowerCase().includes(q)),tm=X.t.map(n=>n.toLowerCase().includes(q));
 const R=X.p.filter(p=>jm[p[2]]||jm[p[3]]||tm[p[4]]).reverse();
 E("cuenta").textContent=`${R.length.toLocaleString("es")} partidos en todas las temporadas`;
 E("vacio").hidden=R.length>0;
 const ron=v=>typeof v==="number"?(RON[X.r[v]]||X.r[v]):v;
 L.innerHTML=R.slice(0,tope).map(p=>`<button class="pit${p[8]?" dp":""}" data-y="${p[0]}" data-i="${p[1]}">
  <div class="f mono">${p[0]}<br>${p[7].split("-").reverse().join("/")}</div>
  <div><div class="j"><b>${esc(X.j[p[2]])}</b> <span>venció a</span> ${esc(X.j[p[3]])}</div>
   <div class="mt">${esc(p[6])} · ${esc(X.t[p[4]])} · ${ron(p[5])}</div></div>
  <div class="der">${p[8]?'<span class="sello-dp">★ ANÁLISIS PROFUNDO</span>':""}</div></button>`).join("");
 E("mas").hidden=R.length<=tope;
 L.querySelectorAll(".pit").forEach(b=>b.onclick=async()=>{
  const y=b.dataset.y,i=+b.dataset.i;
  if(y!==ANIO){await cambiarTemporada(y,true)}
  abrirP(i)})}
function rellenarFiltros(){
 ["fs","ft","fr"].forEach(id=>{const s=E(id);s.length=1});
 const uq=k=>[...new Set(P.map(p=>p[k]).filter(Boolean))].sort();
 uq("s").forEach(v=>E("fs").insertAdjacentHTML("beforeend",`<option value="${v}">${SUPN[v]||v}</option>`));
 uq("t").forEach(v=>E("ft").insertAdjacentHTML("beforeend",`<option value="${esc(v)}">${esc(v)}</option>`));
 ["F","SF","QF","R16","R32","R64","R128","RR"].filter(r=>P.some(p=>p.r===r)).forEach(v=>
  E("fr").insertAdjacentHTML("beforeend",`<option value="${v}">${RON[v]}</option>`))}
async function cambiarTemporada(y,silencio){
 E("cuenta").textContent="cargando la temporada "+y+"…";
 try{await cargarTemporada(y)}catch(e){E("cuenta").textContent="no se pudo cargar "+y;console.error(e);return}
 E("fy").value=y;rellenarFiltros();
 if(!silencio)filtrar();
 if(listos.has("lab")){try{compInit()}catch(e){}}
 if(vistaAct==="lab")montar("lab")}
function vs(a,b,et,f=v=>v,mej="alto"){let ca="",cb="";
 if(a!=null&&b!=null&&a!==b){const g=(mej==="alto")===(a>b);ca=g?"win":"";cb=g?"":"win"}
 return `<div class="vr"><span class="n2 l ${ca}">${a==null?"—":f(a)}</span><span class="et">${et}${tipMed(et)}</span><span class="n2 ${cb}">${b==null?"—":f(b)}</span></div>`}
/* medida con contexto: valor + posición real frente a todo el circuito */
function pctil(k,v){
 const r=D.ref&&D.ref[k];if(!r||v==null)return null;
 const q=r.q;let i=0;while(i<q.length&&q[i]<v)i++;
 return Math.max(0,Math.min(100,i*5));
}
function med(lb,sub,v,esc,col,k){
 if(v==null||v==="")return `<div class="sr"><div class="row"><div class="lb">${lb}<small>${sub}</small></div><div class="vv" style="color:var(--muted)">—</div></div></div>`;
 const r=(k&&D.ref&&D.ref[k])||null;
 let bar="",nota="";
 if(r&&typeof v==="number"){
  const p=pctil(k,v);
  const lo=r.min,hi=r.max;
  const pos=Math.max(0,Math.min(100,100*(v-lo)/(hi-lo)));
  const pm=Math.max(0,Math.min(100,100*(r.med-lo)/(hi-lo)));
  bar=`<div class="eb"><i data-w="${pos}" style="background:${col||'var(--acc)'}"></i><u style="left:${pm}%"></u></div>
   <div class="escn"><span>${lo}</span><span>corriente ${r.med}</span><span>${hi}</span></div>`;
  nota=p>=97?"entre los más altos del circuito":p>=85?`más alto que el ${p}% de los partidos`:
       p<=3?"entre los más bajos del circuito":p<=15?`más bajo que el ${100-p}% de los partidos`:
       `en la zona normal · ${p>50?"por encima":"por debajo"} de la mitad`;
 }else if(esc&&typeof v==="number"){
  const[a,b,m]=esc,pos=Math.max(0,Math.min(100,100*(v-a)/(b-a))),pm=100*(m-a)/(b-a);
  bar=`<div class="eb"><i data-w="${pos}" style="background:${col||'var(--acc)'}"></i><u style="left:${pm}%"></u></div>
   <div class="escn"><span>${a}</span><span>corriente ${m}</span><span>${b}</span></div>`;
 }
 return `<div class="sr"><div class="row"><div class="lb">${lb}${tipMed(lb)}<small>${sub}</small></div>\n  <div class="vv">${v}</div></div>${bar}${nota?`<div class="nota">${nota}</div>`:""}</div>`;
}

function abrirP(i){const p=P[i];
 const pcn=v=>v==null?null:Math.round(v*1000)/10+"%";
 E("pT").innerHTML=`<div style="font-family:var(--sans);font-weight:600;font-size:12px;color:var(--muted);margin-bottom:10px">${esc(p.t)} · ${RON[p.r]||p.r} · ${SUPN[p.s]||p.s}${p["in"]?" · cubierto":""} · ${fF(p.d)}</div>
  <h2 style="font-size:clamp(23px,4vw,34px)">${esc(p.w)} <span style="color:var(--muted);font-weight:400">venció a</span> ${esc(p.l)}</h2>
  <div class="mono" style="font-size:clamp(19px,3.2vw,27px);font-weight:700;margin-top:12px;letter-spacing:-.02em">${esc(p.sc)}</div>
  <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">
   ${p.dp?'<span class="sello-dp">★ ANÁLISIS PROFUNDO</span>':""}
   <span class="tg2" style="color:${COL[p.tp]}">${NOM[p.tp]}</span>
   ${p.rb?'<span class="tg2" style="color:#B478FF">robó el partido</span>':""}
   ${p.vu?'<span class="tg2" style="color:var(--acc)">remontada</span>':""}
   ${p.mi?`<span class="tg2" style="color:var(--muted)">${p.mi} min</span>`:""}
   ${p.rkw&&p.rkl?`<span class="tg2" style="color:var(--muted)">#${p.rkw} vs #${p.rkl}</span>`:""}</div>
  <div style="margin-top:16px;font-family:var(--sans);font-weight:600;font-size:11px;color:var(--muted)">55 medidas calculadas automáticamente</div>`;
 const B=(t)=>`<div class="colt">${t}</div>`;
 E("pB").innerHTML=`<div class="cols"><div>
  ${B("saque · cara a cara")}
  ${vs(p.psw,p.psl,"% puntos al saque",pcn)}
  ${vs(p.p1w,p.p1l,"% primeros dentro",pcn)}
  ${vs(p.g1w,p.g1l,"% gana con el 1º",pcn)}
  ${vs(p.g2w,p.g2l,"% gana con el 2º",pcn)}
  ${vs(p.aw,p.al,"saques directos")}
  ${vs(p.arw,p.arl,"tasa de aces",pcn)}
  ${vs(p.dfw,p.dfl,"dobles faltas",v=>v,"bajo")}
  ${vs(p.adw,p.adl,"aces por doble falta")}
  ${vs(p.pjw,p.pjl,"puntos por juego servido",v=>v,"bajo")}
  ${B("resto · cara a cara")}
  ${vs(p.prw,p.prl,"% puntos al resto",pcn)}
  ${vs(p.bgw,p.bgl,"b. break generadas")}
  ${vs(p.bcw,p.bcl,"% b. break convertidas",pcn)}
  ${B("presión · cara a cara")}
  ${vs(p.bsw,p.bsl,"% b. break salvadas",pcn)}
  ${vs(p.prew,p.prel,"b. break sufridas por juego",v=>v,"bajo")}
  ${B("estructura del marcador")}
  ${med("Sets","jugados",p.ns)}
  ${med("Margen de juegos","diferencia total de juegos",p.mj,null,null,"mj")}
  ${med("Juegos","ganador · perdedor",p.jg!=null?p.jg+" – "+p.jp:null)}
  ${med("Sets ajustados","decididos por 2 juegos o menos",p.sa)}
  ${med("Sets de paliza","decididos por 4 o más",p.sp)}
  ${med("Tiebreaks","jugados · ganados",p.tb!=null?p.tb+" · "+p.tbg:null)}
  ${med("Margen en el tiebreak","cómo de cómodo fue el desempate",p.tbm,null,null,"tbm")}
  ${med("Roscos dados","sets ganados 6-0",p.rd)}
  ${med("Roscos recibidos","sets perdidos 0-6",p.rr)}
  ${med("Ganó el primer set","",p.g1?"sí":"no")}
  ${med("Remontada","perdió el 1º y ganó",p.vu?"sí":"no")}
  ${med("Set decisivo","llegó al último posible",p.sd?"sí":"no")}
 </div><div>
  ${B("lo apretado que estuvo")}
  ${med("Tensión","lo cerca que estuvo de girar",p.te,null,"var(--acc)","te")}
  ${med("Volatilidad","vaivén entre sets",p.vo,null,"#B478FF","vo")}
  ${med("Trayectoria","fue a más (+) o a menos (−) según avanzaba",p.tr,null,"#B478FF","tr")}
  ${B("lo que costó cada juego")}
  ${med("Disputa","lo que costó cada juego",p.di,null,"#1FD68A","di")}
  ${med("Puntos por juego","el mínimo posible son 4",p.ppj,null,"#1FD68A","ppj")}
  ${med("Puntos totales","jugados entre los dos",p.pt,null,null,"pt")}
  ${med("Minutos por punto","ritmo del partido",p.mpp,null,null,"mpp")}
  ${med("Desgaste","volumen de juego ponderado por duración",p.dsg,null,"#FFB74D","dsg")}
  ${B("quién mandaba")}
  ${med("Control del ganador","quién llevaba la iniciativa",p.do,null,"#3D7BFF","do")}
  ${med("Control del perdedor","",p.dop,null,"#3D7BFF","do")}
  ${med("Reparto de puntos","porcentaje del total que se llevó el ganador",p.pp,null,"#B478FF","pp")}
  ${med("Robo","ganó con menos puntos",p.rb?"sí":"no")}
  ${med("Margen del robo","cuánto por debajo del 50% de los puntos",p.mr,null,"#B478FF","mr")}
  ${med("Eficiencia","convirtió puntos sueltos en juegos ganados",p.ef,null,"#1FD68A","ef")}
  ${med("Índice de saques","cerca de 1 significa que nadie rompió",p.isq,null,null,"isq")}
  ${med("Asimetría","cuánto destacó sacando frente a restando",p.asi,null,"#1FD68A","asi")}
  ${B("los momentos que decidieron")}
  ${med("B. break desperdiciadas","oportunidades que dejó escapar",p.de,null,"#FFB74D","de")}
  ${med("Tasa de desperdicio","proporción de las que falló",p.td==null?null:p.td,null,"#FFB74D","td")}
  ${med("Puntos clave ganados","breaks y tiebreaks que decidieron",p.pcl,null,"#FF5C39","pcl")}
  ${med("B. break salvadas de más","frente a las que cabía esperar",p.escp,null,"#FF5C39","escp")}
  ${B("más allá de este partido")}
  ${med("Racha de desgaste","lo que el ganador arrastra de los últimos 7 días",p.rc,null,"#FFB74D","rc")}
  ${med("Rivalidad","tensión media de todos los duelos entre estos dos",p.rivt,null,"#FF5C39","rivt")}
  ${med("Veces que se han cruzado","en todo el histórico del circuito",p.rivn,null,null,"rivn")}
  ${p.rec?`<div class="sr"><div class="row"><div class="lb">Récord personal<small>de la temporada</small></div><div class="vv" style="color:var(--acc);font-size:15px">su partido con más ${p.rec}</div></div></div>`:""}
  ${B("qué significó")}
  ${med("Espectáculo","lo que había en juego por lo reñido que fue",p.es,null,"#FFB74D","es")}
  ${med("Importancia","torneo × ronda · máx 12",p.im,[0,12,4])}
  ${med("Calidad","buen nivel por los dos lados a la vez",p.ca,null,"#FFB74D","ca")}
  ${med("Contundencia","lo claro que fue el resultado",p.pal,null,"#FF5C39","pal")}
  ${med("Sorpresa","lo improbable que era este resultado",p.so,null,"#FF5C39","so")}
  ${B("lectura automática")}
  <p style="font-size:14.5px;color:var(--muted);margin:0 0 10px">${lect(p)}</p>
  <p style="font-size:11.5px;color:var(--muted);opacity:.7;margin:0">Generada por reglas fijas sobre las cifras de arriba. Sin intervención humana ni modelos de lenguaje.</p>
 </div></div>`;
 E("dP").showModal();
 requestAnimationFrame(()=>E("pB").querySelectorAll(".eb i").forEach(b=>b.style.width=b.dataset.w+"%"));
}
function lect(p){const f=[];
 if(p.rb)f.push("Ganó pese a hacer menos puntos que su rival, lo que indica que resolvió mejor los momentos decisivos.");
 if(p.tp==="MARCADOR ENGANOSO")f.push("El marcador parece desequilibrado, pero los juegos se disputaron: la disputa está por encima de la mediana.");
 if(p.tp==="PULSO")f.push("Marcador ajustado y juegos largos a la vez: de los más exigentes que produce el circuito.");
 if(p.tp==="DUELO DE SAQUES")f.push("Marcador ajustado con juegos rápidos: pocos breaks y todo decidido en unos pocos puntos.");
 if(p.tp==="SIN HISTORIA")f.push("Ni el marcador ni los juegos llegaron a estar en juego.");
 if(p.de>=8)f.push(`Desperdició ${p.de} bolas de break, muy por encima de lo normal.`);
 if(p.so>2)f.push("El resultado va bastante en contra de lo que decía el ranking.");
 if(p.vo>3)f.push("Partido de vaivenes: el nivel osciló mucho entre sets.");
 return f.join(" ")||"Partido dentro de los parámetros habituales del circuito en todas las medidas."}



/* ===== EXPLICACIONES AL VUELO ===== */
const EXPL={
 "puntos ganados":"Todos los puntos que se llevó cada uno en el partido entero, sumando los que ganó con su saque y los que le arrancó al saque del rival.",
 "% puntos al saque":"De cada cien puntos que sirvió, cuántos acabó ganando. Lo corriente en el circuito es alrededor de 64. Por debajo de 61 es flojo; por encima de 78, intocable.",
 "% primeros dentro":"De cada cien saques, cuántas veces el primer intento cayó dentro sin recurrir al segundo. La media ronda el 63%.",
 "% gana con el 1º":"Cuando mete el primer saque, con qué frecuencia se lleva el punto. Mide la potencia real del servicio.",
 "% gana con el 2º":"Lo mismo con el segundo saque, que se juega sin red de seguridad. Es la cifra que mejor separa a un jugador bueno de uno corriente.",
 "% b. break salvadas":"De las veces que estuvo a un punto de que le rompieran el saque, cuántas logró salir del apuro. Media del circuito: 60%.",
 "saques directos":"Saques que el rival no llega a tocar. El punto acaba ahí.",
 "tasa de aces":"Saques directos por cada cien puntos servidos. Comparable entre partidos de distinta duración.",
 "dobles faltas":"Las dos veces seguidas que el saque no entra: punto regalado. Aquí menos es mejor.",
 "aces por doble falta":"Cuántos saques directos consigue por cada punto regalado. Mide si el riesgo al servir le compensa.",
 "puntos por juego servido":"Cuánto le cuesta sostener cada juego con su saque. Cuatro es el mínimo posible; por encima de siete está sufriendo.",
 "% puntos al resto":"De los puntos que sirvió el rival, cuántos le quitó. Es la faceta difícil: la media del circuito está en el 36%.",
 "b. break generadas":"Cuántas veces se puso a un punto de romper el saque del rival.",
 "% b. break convertidas":"De esas oportunidades, cuántas aprovechó de verdad.",
 "b. break sufridas por juego":"Cuántas veces por juego se vio con el saque en peligro. Menos es mejor.",
 "Sets":"Sets que hicieron falta para cerrar el partido.",
 "Margen de juegos":"Diferencia total de juegos entre los dos. Ojo: se puede ganar un partido con menos juegos totales.",
 "Juegos":"Juegos que se llevó cada uno en todo el encuentro.",
 "Sets ajustados":"Sets que se decidieron por dos juegos o menos.",
 "Sets de paliza":"Sets que cayeron por cuatro juegos o más.",
 "Tiebreaks":"Desempates que se jugaron y cuántos ganó el vencedor.",
 "Margen en el tiebreak":"Cómo de cómodo fue el desempate: siete menos los puntos que hizo el rival. Un 7-0 da siete; un 7-5, dos.",
 "Roscos dados":"Sets ganados 6-0.",
 "Roscos recibidos":"Sets perdidos 0-6.",
 "Ganó el primer set":"Quien se lleva el primer set gana el partido en torno al 80% de las veces.",
 "Remontada":"Perdió el primer set y aun así ganó el partido.",
 "Set decisivo":"El partido llegó hasta el último set posible, así que se decidió a cara o cruz.",
 "Tensión":"Lo cerca que estuvo el marcador de caer del otro lado. Mira set por set cuánto le faltó al perdedor y hace la media. Cero es un paseo, cien es todo al límite. Lo corriente son 58.",
 "Volatilidad":"Si el partido fue estable o de vaivenes. Un 6-4 6-4 da cero; un 6-1 1-6 6-1 se dispara, aunque el margen final sea parecido.",
 "Trayectoria":"Si el jugador fue a más o a menos según avanzaba el encuentro. Positivo, se creció; negativo, se le fue escapando.",
 "Disputa":"Lo que costó cada juego por dentro, que el marcador no guarda. Se calcula dividiendo los puntos del partido entre los juegos. Un juego en blanco cuesta cuatro puntos; uno que va a deuce, seis o más. Lo corriente son 6,4 puntos por juego.",
 "Puntos por juego":"Los puntos que hizo falta jugar de media para resolver cada juego. Cuatro es el mínimo físico posible.",
 "Puntos totales":"Puntos jugados entre los dos en todo el partido.",
 "Minutos por punto":"El ritmo del encuentro. Alto significa peloteos largos o juego lento.",
 "Desgaste":"Coste físico del partido: combina cuántos puntos se jugaron con cuánto duró. Sirve para seguir la fatiga dentro de un torneo.",
 "Control del ganador":"Quién llevaba la iniciativa. Compara lo que le arranca al rival cuando saca el otro con lo que él mismo cede al servir. Por encima de uno, mandaba él. Lo corriente es 1,32.",
 "Control del perdedor":"Lo mismo para el que perdió. Si es mayor que el del ganador, quien llevó la iniciativa acabó perdiendo el partido.",
 "Reparto de puntos":"Qué porcentaje de todos los puntos del partido se llevó el ganador. Por debajo del 50% significa que ganó haciendo menos puntos que su rival.",
 "Ganó con menos puntos":"Se llevó el partido habiendo ganado menos puntos que el rival. Pasa en uno de cada veinte encuentros, porque en tenis importa cuándo ganas los puntos, no cuántos.",
 "Margen del robo":"Cuánto por debajo de la mitad quedó el ganador en el recuento de puntos.",
 "Eficiencia":"Si colocó los puntos donde hacían falta. Compara el porcentaje de juegos que ganó con el de puntos. Positivo significa que ganó más juegos de los que le tocaban por puntos.",
 "Índice de saques":"Cerca de uno significa que casi nadie rompió el saque del otro. La media del circuito es 0,79.",
 "Asimetría":"Si destacó más sacando o restando, comparado con lo que hace un jugador corriente. Cero significa que sobresalió igual en las dos facetas.",
 "B. break desperdiciadas":"Oportunidades de romper el saque que tuvo y no aprovechó.",
 "Tasa de desperdicio":"Qué proporción de sus oportunidades de break dejó escapar.",
 "Puntos clave ganados":"Cómo le fue en los momentos que deciden: bolas de break a favor y en contra, y desempates.",
 "B. break salvadas de más":"Cuántas bolas de break salvó por encima de las que le tocaban. En el circuito se salvan seis de cada diez, así que esto compara lo que hizo con lo esperable. Un dos significa dos más de las previstas.",
 "Espectáculo":"Combina lo que había en juego con lo reñido que estuvo. Una final de Grand Slam al límite es el máximo; una primera ronda de torneo pequeño, aunque sea igualadísima, puntúa menos.",
 "Importancia":"Peso del torneo multiplicado por el de la ronda. El máximo, doce, es una final de Grand Slam.",
 "Calidad":"Buen nivel por los dos lados a la vez. Un partido tenso entre dos jugadores que fallan mucho no puntúa alto.",
 "Contundencia":"Lo claro que fue el resultado, contando roscos y sets muy desequilibrados.",
 "Sorpresa":"Lo improbable que era este resultado según la clasificación. No resta puestos, los divide: que el 175 gane al número uno pesa mucho más que que el 60 gane al 50.",
 "Racha de desgaste":"Carga acumulada por el ganador en los siete días anteriores. Alta significa que llega cansado al siguiente partido.",
 "Rivalidad":"Tensión media de todos los enfrentamientos que estos dos han tenido en el histórico. Alta significa que suelen producir buenos partidos.",
 "Veces que se han cruzado":"Cuántas veces se han enfrentado en todo el histórico del circuito.",
 "Superficie":"Tierra, pista dura o hierba. Cada una cambia el peso del saque y la frecuencia de los breaks.",
 "Recinto":"Si se jugó bajo techo o al aire libre. Bajo techo no hay viento ni sol, y el saque gana algo de ventaja."
};
function tipMed(txt){
 return EXPL[txt]?`<button class="ast" data-ex="${esc(EXPL[txt])}" aria-label="Qué significa">*</button>`:"";
}

/* ===== PULSO DEL PARTIDO ===== */
function pulso(cv,sets,nomW,nomL,col){
 const o=cx2(cv,190);if(!o)return;const{x,W,H}=o;
 const n=sets.length,pad=42;
 let acum=0;const pts=[[pad,H/2]];
 sets.forEach((s,i)=>{acum+=(s[0]-s[1]);pts.push([pad+(W-pad-14)*(i+1)/n,H/2-acum*(H*.30)/8])});
 x.strokeStyle=cssv("--line");x.lineWidth=1;x.setLineDash([4,5]);
 x.beginPath();x.moveTo(pad,H/2);x.lineTo(W-14,H/2);x.stroke();x.setLineDash([]);
 const g=x.createLinearGradient(0,0,0,H);
 g.addColorStop(0,col+"44");g.addColorStop(1,col+"00");
 x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));
 x.lineTo(W-14,H/2);x.closePath();x.fillStyle=g;x.fill();
 x.beginPath();pts.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));
 x.strokeStyle=col;x.lineWidth=2.6;x.lineJoin="round";x.stroke();
 pts.forEach((q,i)=>{if(!i)return;x.fillStyle=col;x.beginPath();x.arc(q[0],q[1],4.5,0,7);x.fill();
  x.fillStyle=cssv("--muted");x.font="11px 'Space Mono',monospace";x.textAlign="center";
  x.fillText(sets[i-1][0]+"-"+sets[i-1][1],q[0],H-9)});
 x.fillStyle=cssv("--ink");x.font="600 11.5px Sora";x.textAlign="left";
 x.fillText(nomW.split(" ").slice(-1)[0],6,16);
 x.fillStyle=cssv("--muted");x.fillText(nomL.split(" ").slice(-1)[0],6,H-26);
}

/* ===== RADAR COMPARATIVO ===== */
function radar(cv,ejes,col1,col2){
 const o=cx2(cv,280);if(!o)return;const{x,W,H}=o;
 const cxp=W/2,cyp=H/2+4,R=Math.min(W,H)*.30,n=ejes.length;
 const ang=i=>-Math.PI/2+i*2*Math.PI/n;
 x.strokeStyle=cssv("--line");x.lineWidth=1;
 [.25,.5,.75,1].forEach(f=>{x.beginPath();
  for(let i=0;i<=n;i++){const a=ang(i%n),px=cxp+Math.cos(a)*R*f,py=cyp+Math.sin(a)*R*f;
   i?x.lineTo(px,py):x.moveTo(px,py)}x.stroke()});
 for(let i=0;i<n;i++){const a=ang(i);x.beginPath();x.moveTo(cxp,cyp);
  x.lineTo(cxp+Math.cos(a)*R,cyp+Math.sin(a)*R);x.stroke()}
 const poly=(vals,col,alpha)=>{
  x.beginPath();vals.forEach((v,i)=>{const a=ang(i),r=R*Math.max(.05,Math.min(1,v));
   const px=cxp+Math.cos(a)*r,py=cyp+Math.sin(a)*r;i?x.lineTo(px,py):x.moveTo(px,py)});
  x.closePath();x.fillStyle=col;x.globalAlpha=alpha;x.fill();x.globalAlpha=1;
  x.strokeStyle=col;x.lineWidth=2;x.stroke();
  vals.forEach((v,i)=>{const a=ang(i),r=R*Math.max(.05,Math.min(1,v));
   x.fillStyle=col;x.beginPath();x.arc(cxp+Math.cos(a)*r,cyp+Math.sin(a)*r,3,0,7);x.fill()})};
 poly(ejes.map(e=>e.b),col2,.16);
 poly(ejes.map(e=>e.a),col1,.22);
 x.font="600 10.5px Sora";x.fillStyle=cssv("--muted");
 ejes.forEach((e,i)=>{const a=ang(i),d=R+16;
  const px=cxp+Math.cos(a)*d,py=cyp+Math.sin(a)*d;
  x.textAlign=Math.abs(Math.cos(a))<.3?"center":(Math.cos(a)>0?"left":"right");
  x.textBaseline=Math.sin(a)>.5?"top":(Math.sin(a)<-.5?"bottom":"middle");
  x.fillText(e.n,px,py);
  if(e.va!=null){x.font="700 10.5px 'Space Mono',monospace";
   const dy=x.textBaseline==="top"?13:(x.textBaseline==="bottom"?-13:13);
   x.fillStyle=col1;x.fillText(e.va,px-(x.textAlign==="center"?15:0),py+dy);
   x.fillStyle=cssv("--muted");x.fillText(e.vb,px+(x.textAlign==="center"?15:(x.textAlign==="left"?34:-34)),py+dy);
   x.font="600 10.5px Sora";x.fillStyle=cssv("--muted")}});
}
function cx2(cv,h){if(!cv)return null;const r=cv.getBoundingClientRect();if(!r.width)return null;
 const d=Math.min(devicePixelRatio||1,2);cv.width=r.width*d;cv.height=h*d;cv.style.height=h+"px";
 const x=cv.getContext("2d");x.scale(d,d);return{x,W:r.width,H:h}}

/* ===== NAVEGACIÓN ENTRE VISTAS ===== */
const TEMA={home:"night",archivo:"clay",que:"hard",lab:"grass",semana:"paper"};
let vistaAct="home";
const listos=new Set();
function ir(v){
 if(!TEMA[v])return;
 vistaAct=v;
 document.querySelectorAll(".vista").forEach(el=>el.classList.toggle("on",el.id==="v-"+v));
 document.body.dataset.s=TEMA[v];
 document.querySelectorAll(".tnav button").forEach(b=>b.classList.toggle("on",b.dataset.ir===v));
 scrollTo({top:0,behavior:"instant"});
 setTimeout(()=>montar(v),60);
 document.querySelectorAll("#v-"+v+" .rv").forEach((el,i)=>{
  setTimeout(()=>el.classList.add("in"),40+i*70)});
}
function montar(v){
 try{
  if(v==="archivo"&&!listos.has("archivo")){listos.add("archivo");filtrar()}
  if(v==="que"&&!listos.has("que")){listos.add("que");cards()}
  if(v==="lab"){
   plano();mapaEstilos();
   const S=G.tipo_sup;
   barrasPct("gT",S.sup.map(s=>SUPN[s]||s),S.cols,S.pct,200);
   hist("gH",G.h_tension.v,G.h_tension.e,cssv("--acc"),200);
   linea("gA",G.evol.y,G.evol.ace,cssv("--acc"),210);
   linea("gN",G.evol.y,G.evol.ten,"#4D95FF",210);
   if(!listos.has("lab")){listos.add("lab");labInit();compInit()}
  }
  if(v==="semana"&&!listos.has("semana")){listos.add("semana");semanaInit()}
 }catch(e){console.error("[deuce] montar",v,e)}
}

/* ===== LABORATORIO 6-0 ===== */
function labInit(){
 const LAB=[{n:107,ppj:8.9,col:"A"},{n:58,ppj:4.8,col:"B"}];
 LAB.forEach(L=>{const c=E("dots"+L.col);c.innerHTML="";
  for(let i=0;i<L.n;i++)c.appendChild(document.createElement("i"))});
 let T=[];
 const llena=i=>{const L=LAB[i],ds=E("dots"+L.col).querySelectorAll("i"),num=E("num"+L.col);
  ds.forEach(d=>d.classList.remove("on"));num.textContent="0";E("bar"+L.col+"1").style.width="0";
  let k=0;T.push(setInterval(()=>{
   if(k>=L.n||!ds[k]){E("bar"+L.col+"1").style.width=(100*L.ppj/9)+"%";return}
   ds[k].classList.add("on");num.textContent=(++k)},14))};
 const reset=()=>{T.forEach(clearInterval);T=[]};
 document.querySelectorAll(".lab-tab").forEach((b,i)=>b.onclick=()=>{
  document.querySelectorAll(".lab-tab").forEach((x,j)=>x.classList.toggle("on",j===i));
  E("colA").classList.toggle("dim",i===1);E("colB").classList.toggle("dim",i===0);
  reset();llena(i)});
 E("labPlay").onclick=()=>{reset();E("colA").classList.remove("dim");E("colB").classList.remove("dim");
  document.querySelectorAll(".lab-tab").forEach(b=>b.classList.remove("on"));llena(0);llena(1)};
 E("colB").classList.add("dim");llena(0);
}

/* ===== COMPARADOR DE DOS PARTIDOS ===== */
function compInit(){
 const CAMPOS=[["te","tensión",100],["di","disputa",100],["es","espectáculo",12],
   ["do","control",3],["vo","volatilidad",6],["pt","puntos jugados",340],["mi","minutos",300]];
 const pool=P.slice().sort((a,b)=>(b.es||0)-(a.es||0)).slice(0,160);
 const et=p=>`${p.w.split(" ").slice(-1)[0]} d. ${p.l.split(" ").slice(-1)[0]} · ${p.t} · ${p.sc}`;
 const sa=E("cmpA"),sb=E("cmpB");
 sa.innerHTML=sb.innerHTML="";
 pool.forEach((p,i)=>{
  sa.insertAdjacentHTML("beforeend",`<option value="${i}">${esc(et(p))}</option>`);
  sb.insertAdjacentHTML("beforeend",`<option value="${i}">${esc(et(p))}</option>`)});
 sa.value=0;sb.value=1;
 const pinta=()=>{
  const A=pool[+sa.value],B=pool[+sb.value];
  const card=(p,der)=>`<div style="text-align:${der?"left":"right"}">
   <div class="cn">${esc(p.w)}</div>
   <div class="cm">venció a ${esc(p.l)}</div>
   <div class="cs">${esc(p.sc)}</div>
   <div class="cm">${esc(p.t)} · ${RON[p.r]||p.r} · ${fF(p.d)}</div></div>`;
  E("cmpCab").innerHTML=card(A,false)+'<div class="vs">vs</div>'+card(B,true);
  E("cmpFilas").innerHTML=CAMPOS.map(([c,n,mx])=>{
   const va=A[c],vb=B[c],ga=(va||0)>=(vb||0);
   return `<div class="cf"><div class="cft">${n}${tipMed(n.charAt(0).toUpperCase()+n.slice(1))}</div>
    <div class="cfr">
     <div class="cb izq"><i data-w="${100*Math.min(1,(va||0)/mx)}" style="background:${ga?"var(--acc)":"rgba(255,255,255,.22)"}"></i></div>
     <div class="cv"><b style="color:${ga?"var(--acc)":"var(--ink)"}">${va??"—"}</b> · <b style="color:${!ga?"var(--acc)":"var(--ink)"}">${vb??"—"}</b></div>
     <div class="cb"><i data-w="${100*Math.min(1,(vb||0)/mx)}" style="background:${!ga?"var(--acc)":"rgba(255,255,255,.22)"}"></i></div>
    </div></div>`}).join("");
  requestAnimationFrame(()=>E("cmpFilas").querySelectorAll("[data-w]").forEach(el=>el.style.width=el.dataset.w+"%"));
 };
 sa.onchange=pinta;sb.onchange=pinta;
 E("cmpAzar").onclick=()=>{sa.value=Math.floor(Math.random()*pool.length);
  sb.value=Math.floor(Math.random()*pool.length);pinta()};
 pinta();
}

/* ===== PARTIDO DE LA SEMANA ===== */
function semanaInit(){
 const s=CUR.semana;if(!s)return;
 E("perH").innerHTML=`${esc(s.w)}<em>venció a</em>${esc(s.l)}`;
 E("perSc").textContent=s.sc;
 E("perMeta").textContent=`${s.t} · ${RON[s.r]||s.r} · ${SUPN[s.s]||s.s} · ${fF(s.d)} · ${s.mi} minutos`;
 const k=[["te","tensión",s.te],["di","disputa",s.di],["es","espectáculo",s.es],
          ["pt","puntos",(s.pg+s.pl)],["do","control",s.do],["tb","tiebreaks",s.tb]];
 E("perKpi").innerHTML=k.map(([c,n,v])=>`<div class="pk"><b class="mono">${v??"—"}</b><span>${n}</span></div>`).join("");
 const dif=s.st.map(x=>x[0]-x[1]);
 const rel=s.st.map((x,i)=>{
  const d=x[0]-x[1];
  const txt = d>=4 ? "Se lo llevó sin discusión. La diferencia de juegos no deja lugar a la interpretación."
   : d<0 ? "Aquí perdió el hilo. El rival se llevó el set y el encuentro cambió de manos."
   : Math.abs(d)<=1 ? "Set decidido por un puñado de puntos, de los que podrían haber caído para cualquiera."
   : "Set peleado, aunque acabó resolviéndose en un par de juegos clave.";
  return `<div class="paso"><div class="ps mono">${x[0]}-${x[1]}</div>
   <div class="pt">${txt}</div>
   <div class="pd"><div>juegos<b>${x[0]+x[1]}</b></div>
    <div>diferencia<b>${d>0?"+":""}${d}</b></div>
    <div>set<b>${i+1} de ${s.st.length}</b></div></div></div>`}).join("");
 const cierre=`<div class="paso"><div class="ps mono">${s.pg}–${s.pl}</div>
  <div class="pt">Puntos totales del encuentro. ${s.rb?"<b>Ganó haciendo menos puntos que su rival</b>, lo que indica que resolvió mejor los momentos decisivos.":"El reparto de puntos acompañó al resultado."}
  La disputa quedó en <b>${s.di}</b> y la tensión en <b>${s.te}</b>, con ${s.tb} desempate${s.tb==1?"":"s"} por medio.</div>
  <div class="pd"><div>aces<b>${s.aw}–${s.al}</b></div>
   <div>bolas de break salvadas<b>${Math.round((s.bsw||0)*100)}% – ${Math.round((s.bsl||0)*100)}%</b></div>
   <div>puntos al saque<b>${Math.round((s.psw||0)*100)}% – ${Math.round((s.psl||0)*100)}%</b></div>
   <div>oportunidades falladas<b>${s.de}</b></div></div></div>
  <div class="paso"><canvas id="swPulso"></canvas>
   <div class="pt" style="margin-top:10px">El pulso del encuentro, set a set. Por encima de la línea manda el ganador.</div></div>`;
 E("rel").innerHTML=rel+cierre;
 const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add("in")}),{threshold:.35});
 E("rel").querySelectorAll(".paso").forEach(el=>io.observe(el));
 setTimeout(()=>pulso(E("swPulso"),s.st,s.w,s.l,cssv("--acc")),400);
}

/* ===== FICHA CON PULSO Y RADAR ===== */
const _abrirP=abrirP;
abrirP=function(i){
 _abrirP(i);
 const p=P[i];
 const viz=document.createElement("div");
 viz.className="viz2";
 viz.innerHTML=`<div class="vbox"><h4>El pulso del partido <button class="ast" data-ex="La línea sube cuando el ganador se lleva un set y baja cuando lo pierde, con la altura proporcional a la diferencia de juegos. Sirve para ver de un vistazo si el partido fue de menos a más, si hubo remontada o en qué set se rompió el encuentro.">*</button></h4>
   <p>Cómo se movió la ventaja, set a set</p><canvas id="vzPulso"></canvas></div>
  <div class="vbox"><h4>Perfil comparado <button class="ast" data-ex="Cada punta es un porcentaje clásico del tenis, y junto a ella van las dos cifras reales: la naranja del ganador y la gris del perdedor. Cuanto más lejos del centro, mejor. Cada eje va de lo flojo a lo excelente según lo que se ve en el circuito, para que las diferencias se aprecien. Si un polígono envuelve al otro, ganó siendo mejor en todo; si se cruzan, cada uno fue superior en cosas distintas.">*</button></h4>
   <p>Seis porcentajes clásicos del partido. Naranja el ganador, gris el perdedor, con sus cifras en cada punta</p><canvas id="vzRadar"></canvas></div>`;
 const body=E("pB");body.insertBefore(viz,body.firstChild);
 const pr=p.dp?PROF[p.k]:null, dp=pr?pr.deep:null;
 if(dp){body.insertBefore(bloqueProfundo(p,dp),body.firstChild);
  try{marcadorVivo(E("dpTv"),p,dp)}catch(e){console.error("[deuce] marcador",e)}}
 requestAnimationFrame(()=>{
  try{
   if(p.st&&p.st.length)pulso(E("vzPulso"),p.st,p.w,p.l,cssv("--acc"));
   const nrm=(v,lo,hi)=>v==null?0:Math.max(0,Math.min(1,(v-lo)/(hi-lo)));
   const pcn=v=>v==null?"—":Math.round(v*100)+"%";
   radar(E("vzRadar"),[
    {n:"puntos al saque",a:nrm(p.psw,.50,.85),b:nrm(p.psl,.50,.85),va:pcn(p.psw),vb:pcn(p.psl)},
    {n:"puntos al resto",a:nrm(p.prw,.15,.50),b:nrm(p.prl,.15,.50),va:pcn(p.prw),vb:pcn(p.prl)},
    {n:"1º dentro",a:nrm(p.p1w,.45,.80),b:nrm(p.p1l,.45,.80),va:pcn(p.p1w),vb:pcn(p.p1l)},
    {n:"gana con el 1º",a:nrm(p.g1w,.55,.90),b:nrm(p.g1l,.55,.90),va:pcn(p.g1w),vb:pcn(p.g1l)},
    {n:"gana con el 2º",a:nrm(p.g2w,.30,.70),b:nrm(p.g2l,.30,.70),va:pcn(p.g2w),vb:pcn(p.g2l)},
    {n:"b. break salvadas",a:nrm(p.bsw,.20,1),b:nrm(p.bsl,.20,1),va:pcn(p.bsw),vb:pcn(p.bsl)}
   ],cssv("--acc"),cssv("--muted"));
   if(dp){try{cortoLargo(E("dpRally"),p,dp);adondeSaca(E("dpSaque"),p,dp);huellaDoble(E("dpHuella"),p,dp)}
    catch(e){console.error("[deuce] graficos profundos",e)}}
  }catch(e){console.error("[deuce] viz ficha",e)}
 });
};

/* =====================================================================
   ANÁLISIS PROFUNDO · solo para partidos anotados golpe a golpe
   ===================================================================== */
const PTS=["0","15","30","40"];
function marcadorVivo(box,p,dp){
 const inv=dp.j1==="l";                           // el jugador 1 del anotador ¿es el perdedor?
 const W=p.w.split(" ").slice(-1)[0].toUpperCase(),L=p.l.split(" ").slice(-1)[0].toUpperCase();
 const seq=dp.seq,fin=p.st||[];
 // estados punto a punto, siempre orientados GANADOR / PERDEDOR
 const est=[];
 seq.forEach((j,ji)=>{
  let a=0,b=0;const tb=j.g[0]===6&&j.g[1]===6;
  const sv=inv?(j.sv===1?2:1):j.sv;                // 1 = saca el ganador
  const sets=j.s[0]+j.s[1];
  j.p.forEach(w=>{
   const gw=inv?(w===1?2:1):w;
   if(gw===1)a++;else b++;
   let txt;
   if(tb)txt=[a,b];
   else if(a>=3&&b>=3){txt=a===b?["40","40"]:(a>b?["AD",""]:["","AD"])}
   else txt=[PTS[Math.min(a,3)],PTS[Math.min(b,3)]];
   est.push({set:sets,g:inv?[j.g[1],j.g[0]]:j.g,pt:txt,sv,ji})});
 });
 box.innerHTML=`<div class="tv">
  <div class="tv-top"><span>${esc(p.t)} · ${RON[p.r]||p.r}</span><span id="tvPt" class="mono">punto 0 de ${est.length}</span></div>
  <div class="tv-row" data-q="w"><div class="tv-n"><i class="tv-sv"></i>${esc(W)}</div><div class="tv-s"></div><div class="tv-g mono">0</div><div class="tv-p mono">0</div></div>
  <div class="tv-row" data-q="l"><div class="tv-n"><i class="tv-sv"></i>${esc(L)}</div><div class="tv-s"></div><div class="tv-g mono">0</div><div class="tv-p mono">0</div></div>
  <div class="tv-ctl"><button class="tv-b" data-a="play">▶ Reproducir el partido</button>
   <input type="range" min="0" max="${est.length}" value="0" class="tv-r" aria-label="Avanzar por el partido">
   <select class="tv-v" aria-label="Velocidad"><option value="90">normal</option><option value="35" selected>rápido</option><option value="10">muy rápido</option></select></div>
  <div class="tv-nota">Reproducción real, punto a punto, a partir de la anotación del partido. No es una simulación.</div></div>`;
 const R=box.querySelector(".tv-r"),rw=box.querySelector('[data-q="w"]'),rl=box.querySelector('[data-q="l"]');
 const pinta=i=>{
  const e=est[Math.max(0,Math.min(est.length-1,i-1))];
  if(i===0){rw.querySelector(".tv-s").innerHTML=rl.querySelector(".tv-s").innerHTML="";
   rw.querySelector(".tv-g").textContent=rl.querySelector(".tv-g").textContent="0";
   rw.querySelector(".tv-p").textContent=rl.querySelector(".tv-p").textContent="0";
   box.querySelector("#tvPt").textContent=`punto 0 de ${est.length}`;return}
  const cerr=fin.slice(0,e.set);
  rw.querySelector(".tv-s").innerHTML=cerr.map(s=>`<b class="${s[0]>s[1]?"gan":""}">${s[0]}</b>`).join("");
  rl.querySelector(".tv-s").innerHTML=cerr.map(s=>`<b class="${s[1]>s[0]?"gan":""}">${s[1]}</b>`).join("");
  rw.querySelector(".tv-g").textContent=e.g[0];rl.querySelector(".tv-g").textContent=e.g[1];
  rw.querySelector(".tv-p").textContent=e.pt[0];rl.querySelector(".tv-p").textContent=e.pt[1];
  rw.classList.toggle("sv",e.sv===1);rl.classList.toggle("sv",e.sv===2);
  box.querySelector("#tvPt").textContent=`punto ${i} de ${est.length}`;
  if(i>=est.length){ // marcador final
   rw.querySelector(".tv-s").innerHTML=fin.map(s=>`<b class="${s[0]>s[1]?"gan":""}">${s[0]}</b>`).join("");
   rl.querySelector(".tv-s").innerHTML=fin.map(s=>`<b class="${s[1]>s[0]?"gan":""}">${s[1]}</b>`).join("");
   rw.querySelector(".tv-g").textContent=rl.querySelector(".tv-g").textContent="";
   rw.querySelector(".tv-p").textContent="✓";rl.querySelector(".tv-p").textContent=""}
 };
 let T=null;
 R.oninput=()=>{clearInterval(T);pinta(+R.value)};
 box.querySelector('[data-a="play"]').onclick=()=>{clearInterval(T);if(+R.value>=est.length)R.value=0;
  T=setInterval(()=>{if(+R.value>=est.length){clearInterval(T);return}R.value=+R.value+1;pinta(+R.value)},+box.querySelector(".tv-v").value)};
 pinta(0);
}

/* ---- recuentos puros, cara a cara ---- */
function recuentos(p,dp){
 const A=dp.J.w||{},B=dp.J.l||{};
 const n=v=>v==null?null:Math.round(v);
 const F=[
  ["golpes ganadores",A.win,B.win,"alto","Golpes que el rival no llegó a tocar o no pudo devolver dentro. El punto acaba ahí, a favor de quien golpea."],
  ["· con la derecha",A.wfh,B.wfh,"alto",null],["· con el revés",A.wbh,B.wbh,"alto",null],
  ["errores no forzados",A.ue,B.ue,"bajo","Fallos sin presión del rival: la bola era jugable y el propio jugador la mandó fuera o a la red. Aquí menos es mejor."],
  ["· con la derecha",A.ufh,B.ufh,"bajo",null],["· con el revés",A.ubh,B.ubh,"bajo",null],
  ["ganadores menos errores",A.win!=null&&A.ue!=null?A.win-A.ue:null,B.win!=null&&B.ue!=null?B.win-B.ue:null,"alto","Saldo entre lo que regaló y lo que se ganó por su cuenta. Positivo significa que decidió más puntos a su favor de los que tiró."],
  ["subidas a la red",A.net,B.net,"alto","Puntos en los que el jugador se acercó a la red para terminar el intercambio."],
  ["· ganadas",A.netw,B.netw,"alto",null],["· ganadores en la red",A.netg,B.netg,"alto",null],
  ["passings recibidos",A.pas,B.pas,"bajo","Veces que subió a la red y el rival le pasó con un golpe que no alcanzó."],
  ["puntos analizados",A.pts,B.pts,"alto","Puntos jugados que figuran en la anotación de este partido."]];
 return `<div class="colt">los recuentos, golpe a golpe · ganador a la izquierda</div>`+
  F.map(([et,a,b,mej,ex])=>{
   let ca="",cb="";if(a!=null&&b!=null&&a!==b){const g=(mej==="alto")===(a>b);ca=g?"win":"";cb=g?"":"win"}
   const sub=et.startsWith("·");
   return `<div class="vr${sub?" sub":""}"><span class="n2 l ${ca}">${n(a)??"—"}</span>
    <span class="et">${et}${ex?`<button class="ast" data-ex="${esc(ex)}" aria-label="Qué significa">*</button>`:""}</span>
    <span class="n2 ${cb}">${n(b)??"—"}</span></div>`}).join("");
}

/* ---- el arma y la grieta, de los dos ---- */
function armaGrieta(p,dp){
 const barra=(t,a,b,col)=>{const tt=(a||0)+(b||0)||1;return `<div class="ag-f">
  <div class="ag-t"><span>derecha ${a??0}</span><span style="color:${col}">${t}</span><span>${b??0} revés</span></div>
  <div class="ag-b"><i style="flex:${a||0};background:${col}">${Math.round(100*(a||0)/tt)}%</i><i style="flex:${b||0};background:${col};opacity:.4">${Math.round(100*(b||0)/tt)}%</i></div></div>`};
 const bloque=(nom,J)=>{
  const arma=(J.wfh||0)>=(J.wbh||0)?"la derecha":"el revés",grieta=(J.ufh||0)>=(J.ubh||0)?"la derecha":"el revés";
  return `<div class="ag"><div class="ag-n">${esc(nom)}</div>
   ${barra("ganadores",J.wfh,J.wbh,"var(--acc)")}${barra("errores",J.ufh,J.ubh,"var(--muted)")}
   <p class="ag-l">Ganó sus puntos sobre todo con <b>${arma}</b> y los regaló sobre todo con <b>${grieta}</b>.
   ${arma===grieta?"Su golpe decisivo fue también el que más falló.":"Arma y punto débil en lados distintos."}</p></div>`};
 return `<div class="colt">el arma y la grieta <button class="ast" data-ex="Qué golpe usó cada uno para ganar puntos y con cuál los perdió por error propio, en este partido. Es un recuento de lo que pasó ese día, no una etiqueta del jugador." aria-label="Qué significa">*</button></div>
  <div class="ag2">${bloque(p.w,dp.J.w||{})}${bloque(p.l,dp.J.l||{})}</div>`;
}

/* ---- corto o largo, los dos en el mismo gráfico ---- */
function cortoLargo(cv,p,dp){
 const o=cx2(cv,260);if(!o)return;const{x,W,H}=o;
 const M={l:48,r:88,t:22,b:44},cats=["1-3","4-6","7-9","10"],et=["1 a 3","4 a 6","7 a 9","10 o más"];
 const px=i=>M.l+(W-M.l-M.r)*i/3,py=v=>H-M.b-(H-M.t-M.b)*v;
 x.strokeStyle=cssv("--line");x.fillStyle=cssv("--muted");x.font="10px 'Space Mono',monospace";x.textAlign="right";
 [0,.25,.5,.75,1].forEach(v=>{x.beginPath();x.moveTo(M.l,py(v));x.lineTo(W-M.r,py(v));x.stroke();x.fillText(Math.round(v*100)+"%",M.l-7,py(v)+3)});
 x.setLineDash([4,5]);x.strokeStyle=cssv("--muted");x.beginPath();x.moveTo(M.l,py(.5));x.lineTo(W-M.r,py(.5));x.stroke();x.setLineDash([]);
 x.textAlign="center";x.font="600 10.5px Sora";et.forEach((t,i)=>x.fillText(t,px(i),H-22));
 x.font="500 10px Sora";x.fillText("golpes por punto",(M.l+W-M.r)/2,H-6);
 [["w",cssv("--acc"),p.w],["l","#8FB2DA",p.l]].forEach(([L,col,nom])=>{
  const R=(dp.J[L]||{}).rally;if(!R)return;
  const v=cats.map(c=>{const[w,n]=R[c]||[0,0];return n>=3?{p:w/n,n}:null});
  x.strokeStyle=col;x.lineWidth=2.8;x.lineJoin="round";x.beginPath();let first=true;
  v.forEach((q,i)=>{if(!q)return;first?x.moveTo(px(i),py(q.p)):x.lineTo(px(i),py(q.p));first=false});x.stroke();
  v.forEach((q,i)=>{if(!q)return;x.fillStyle=col;x.beginPath();x.arc(px(i),py(q.p),4.5,0,7);x.fill();
   x.fillStyle=cssv("--muted");x.font="9.5px 'Space Mono',monospace";x.textAlign="center";
   x.fillText(q.n+"p",px(i),py(q.p)+(L==="w"?-9:16))});
  const last=[...v].reverse().find(q=>q),li=v.lastIndexOf(last);
  if(last){x.fillStyle=col;x.font="700 11.5px Sora";x.textAlign="left";x.fillText(nom.split(" ").slice(-1)[0],px(li)+10,py(last.p)+4)}
 });
}

/* ---- adónde saca, una pista para cada uno ---- */
function adondeSaca(cv,p,dp){
 const o=cx2(cv,230);if(!o)return;const{x,W,H}=o;
 const pista=(ox,cw,sd,nom,col,n)=>{
  const ch=cw*.6,oy=36,half=cw/2,mx=Math.max(...(sd||[0]));
  [[ox,[0,1,2],["abierto","cuerpo","T"]],[ox+half,[5,4,3],["T","cuerpo","abierto"]]].forEach(([x0,ids,nm])=>{
   const zw=half/3;ids.forEach((k,zi)=>{const v=sd?sd[k]||0:0,t=v/(mx||1);
    x.globalAlpha=.1+t*.8;x.fillStyle=col;x.fillRect(x0+zi*zw,oy,zw,ch);x.globalAlpha=1;
    x.fillStyle=t>.55?"#0B0E14":cssv("--ink");x.font="700 "+(11+t*6)+"px 'Space Mono',monospace";x.textAlign="center";
    x.fillText(Math.round(v*100)+"%",x0+zi*zw+zw/2,oy+ch/2+4);
    x.font="600 8.5px Sora";x.fillStyle=cssv("--muted");x.fillText(nm[zi],x0+zi*zw+zw/2,oy+ch-6)})});
  x.strokeStyle=cssv("--ink");x.lineWidth=1.5;x.strokeRect(ox,oy,cw,ch);
  x.beginPath();x.moveTo(ox+half,oy);x.lineTo(ox+half,oy+ch);x.stroke();
  x.lineWidth=3.5;x.beginPath();x.moveTo(ox-6,oy);x.lineTo(ox+cw+6,oy);x.stroke();
  x.fillStyle=col;x.font="700 12px Sora";x.textAlign="center";x.fillText(nom.split(" ").slice(-1)[0],ox+cw/2,20);
  x.fillStyle=cssv("--muted");x.font="10px Sora";x.fillText(`${n||0} primeros saques · iguales | ventaja`,ox+cw/2,oy+ch+18)};
 const cw=Math.min((W-50)/2,300),gap=Math.max(24,W-2*cw-20);
 pista(10,cw,(dp.J.w||{}).sd,p.w,cssv("--acc"),(dp.J.w||{}).sdn);
 pista(10+cw+Math.min(gap,60),cw,(dp.J.l||{}).sd,p.l,"#8FB2DA",(dp.J.l||{}).sdn);
}

/* ---- huella del partido, las dos superpuestas ---- */
function huellaDoble(cv,p,dp){
 const o=cx2(cv,330);if(!o)return;const{x,W,H}=o;
 const dims=J=>{const R=J.rally||{},l=R["10"]||[0,0],pts=J.pts||1;
  const c=(v,a,b)=>v==null||isNaN(v)?.1:Math.max(.08,Math.min(1,(v-a)/(b-a)));
  return[["agresividad",c(((J.win||0)+(J.ue||0))/pts,.15,.55)],["rentabilidad",c((J.win||0)/Math.max(J.ue||1,1),.3,2.2)],
   ["sube a la red",c((J.net||0)/pts,0,.25)],["acierto en red",c((J.netw||0)/Math.max(J.net||1,1),.3,1)],
   ["arma de derecha",c((J.wfh||0)/Math.max((J.wfh||0)+(J.wbh||0),1),.3,1)],["fiabilidad",c(1-(J.ue||0)/pts,.6,.95)],
   ["gana los largos",c(l[1]>=3?l[0]/l[1]:.5,.2,.8)]]};
 const A=dims(dp.J.w||{}),B=dims(dp.J.l||{});
 const cxp=W/2,cyp=H/2+6,R=Math.min(W,H)*.33,n=A.length;
 [.33,.66,1].forEach(f=>{x.strokeStyle=cssv("--line");x.beginPath();x.arc(cxp,cyp,R*f,0,7);x.stroke()});
 const forma=(D,col,al)=>{const P2=[];
  for(let i=0;i<=180;i++){const t=i/180*Math.PI*2-Math.PI/2;let v=0,ws=0;
   D.forEach((r,k)=>{const a=k/n*Math.PI*2-Math.PI/2;let d=Math.abs(t-a);d=Math.min(d,Math.PI*2-d);const w=Math.exp(-(d*d)/.15);v+=r[1]*w;ws+=w});
   const rr=R*(.16+.84*v/ws);P2.push([cxp+Math.cos(t)*rr,cyp+Math.sin(t)*rr])}
  x.beginPath();P2.forEach((q,i)=>i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]));x.closePath();
  x.globalAlpha=al;x.fillStyle=col;x.fill();x.globalAlpha=1;x.strokeStyle=col;x.lineWidth=2.2;x.stroke()};
 forma(B,"#8FB2DA",.22);forma(A,cssv("--acc"),.28);
 x.font="600 10px Sora";x.fillStyle=cssv("--muted");
 A.forEach((r,k)=>{const a=k/n*Math.PI*2-Math.PI/2,d=R+20;
  x.textAlign=Math.abs(Math.cos(a))<.3?"center":(Math.cos(a)>0?"left":"right");x.fillText(r[0],cxp+Math.cos(a)*d,cyp+Math.sin(a)*d+4)});
 x.font="700 11.5px Sora";x.textAlign="left";
 x.fillStyle=cssv("--acc");x.fillText("■ "+p.w.split(" ").slice(-1)[0],10,16);
 x.fillStyle="#8FB2DA";x.fillText("■ "+p.l.split(" ").slice(-1)[0],10,32);
}


/* ---- variables nuevas del análisis profundo ---- */
const MARC=["0","15","30","40"];
function cantaPunto(a,b,tb){               // a = puntos del ganador, b = del perdedor
 if(tb)return a+"-"+b;
 if(a>=3&&b>=3)return a===b?"iguales":(a>b?"ventaja ganador":"ventaja perdedor");
 return MARC[Math.min(a,3)]+"-"+MARC[Math.min(b,3)];
}
function nuevasVars(p,nv){
 if(!nv)return"";
 const A=nv.w||{},B=nv.l||{};
 const fr=x=>x&&x[1]>0?`<span class="nv-n">${x[0]} de ${x[1]}</span><span class="nv-p">${Math.round(100*x[0]/x[1])}%</span>`:'<span class="nv-p">—</span>';
 const pct=x=>x&&x[1]>0?x[0]/x[1]:null;
 const fila=(t,a,b,ex,mej="alto",va,vb)=>{
  const pa=va!==undefined?va:pct(a),pb=vb!==undefined?vb:pct(b);
  let ca="",cb="";if(pa!=null&&pb!=null&&Math.abs(pa-pb)>.005){const g=(mej==="alto")===(pa>pb);ca=g?"win":"";cb=g?"":"win"}
  return `<div class="nv"><div class="nv-v l ${ca}">${a}</div>
   <div class="nv-t">${t}<button class="ast" data-ex="${esc(ex)}" aria-label="Qué significa">*</button></div>
   <div class="nv-v ${cb}">${b}</div></div>`};
 const ev=x=>x?`<span class="nv-p">${x[0]>=x[1]?"−":"+"}${Math.abs(Math.round(100*(x[0]-x[1])))} pts</span><span class="nv-n">${Math.round(100*x[0])}% → ${Math.round(100*x[1])}%</span>`:'<span class="nv-p">—</span>';
 const tp=x=>{if(!x)return'<span class="nv-p">—</span>';const d=x[0]/x[1]-x[2]/x[3];
  return `<span class="nv-p">${d>=0?"+":"−"}${Math.abs(Math.round(100*d))} pts</span><span class="nv-n">${x[0]} de ${x[1]} salvadas · ${Math.round(100*x[2]/x[3])}% en su saque normal</span>`};
 const rc=x=>x?`<span class="nv-p">${x[0]} seguidos</span><span class="nv-n">en el set ${x[1]}</span>`:'<span class="nv-p">—</span>';
 const pwA=A.peso!=null?Math.round(100*A.peso):null, pwB=pwA!=null?100-pwA:null;   // que sumen exactamente 100
 const pw=v=>v!=null?`<span class="nv-p">${v}%</span><span class="nv-n">del peso total del partido</span>`:'<span class="nv-p">—</span>';
 let top="";
 if(nv.top){const t=nv.top,tb=t.g[0]===6&&t.g[1]===6;
  const quien=t.sv==="w"?p.w:p.l,gana=t.gana==="w"?p.w:p.l;
  const mS=t.sv==="w"?[t.p[0],t.p[1]]:[t.p[1],t.p[0]];      // el sacador se canta primero
  const jS=t.sv==="w"?[t.g[0],t.g[1]]:[t.g[1],t.g[0]];
  top=`<div class="nv-top">
   <div class="nv-top-e">el punto que más pesó</div>
   <div class="nv-top-m mono">${tb?"desempate":cantaPunto(mS[0],mS[1],false)} <span>· ${jS[0]}-${jS[1]} en el set ${t.set}</span></div>
   <p>Sacaba <b>${esc(quien)}</b>. Se lo llevó <b>${esc(gana)}</b>. De todos los puntos del encuentro, fue el que más cambió las probabilidades de ganar el partido.</p></div>`}
 return `<div class="colt">más a fondo · ganador a la izquierda</div>
  ${top}
  ${fila("peso de los puntos ganados",pw(pwA),pw(pwB),"No todos los puntos valen lo mismo: perder un 40-0 no cambia nada y perder un 30-40 te cuesta el saque. Aquí cada punto pesa según cuánto cambió la probabilidad de ganar el partido. Esta cifra dice qué parte de ese peso total se llevó cada jugador. Quien gana los puntos que importan suele ganar aunque haga menos puntos en total.","alto",A.peso,B.peso)}
  ${fila("racha más larga",rc(A.racha),rc(B.racha),"El mayor número de puntos seguidos que ganó cada uno, y en qué set llegó. Una racha larga a mitad de partido suele ser el momento exacto en que se rompe el encuentro.","alto",A.racha?A.racha[0]:null,B.racha?B.racha[0]:null)}
  ${fila("liquida con el primer golpe tras sacar",fr(A.s1?[A.s1[0],A.s1[2]]:null),fr(B.s1?[B.s1[0],B.s1[2]]:null),"De los puntos en que el rival devolvió su saque, en cuántos cerró el punto con el siguiente golpe: bien con un ganador, bien forzando el error del rival. Mide si aprovecha la ventaja que le da el saque.")}
  ${fila("ventaja del saque que se evapora",ev(A.evap),ev(B.evap),"Qué porcentaje de puntos gana con el primer saque en general, y qué porcentaje gana cuando el punto se alarga más allá de cinco golpes. La diferencia es cuánta ventaja pierde el saque si el rival consigue alargar el intercambio. Aquí menos es mejor.","bajo",A.evap?A.evap[0]-A.evap[1]:null,B.evap?B.evap[0]-B.evap[1]:null)}
  ${fila("temple en bola de break",tp(A.temple),tp(B.temple),"Cuánto mejor o peor rindió con el saque en peligro que en sus puntos al saque normales. Positivo, apretó en los momentos críticos; negativo, se le escaparon. Es un hecho de este partido: como rasgo del jugador no se sostiene, porque no se repite de un partido a otro.","alto",A.temple?A.temple[0]/A.temple[1]-A.temple[2]/A.temple[3]:null,B.temple?B.temple[0]/B.temple[1]-B.temple[2]/B.temple[3]:null)}
  ${fila("golpes cruzados",fr(A.cruz),fr(B.cruz),"De todos sus golpes de fondo, qué parte fue en diagonal, de un lado de la pista al otro. Es el golpe más seguro porque la pista es más larga en esa dirección y la red más baja en el centro.")}
  ${fila("golpes paralelos",fr(A.par),fr(B.par),"De todos sus golpes de fondo, qué parte fue en línea recta, pegada a la banda. Es el golpe más arriesgado: menos pista y red más alta, pero sorprende al rival y cambia el ritmo.")}
  ${fila("sube a la red tras sacar",fr(A.snv),fr(B.snv),"En cuántos de sus puntos al saque subió directamente a la red nada más sacar, sin esperar al intercambio desde el fondo.")}
  ${fila("restos profundos",fr(A.prof),fr(B.prof),"De sus restos que cayeron dentro, cuántos fueron profundos, cerca de la línea de fondo. Un resto corto regala la iniciativa al que saca; uno profundo se la quita.")}
  ${fila("restos puestos en juego",fr(A.enj),fr(B.enj),"De los saques que se podían devolver, cuántos devolvió dentro de la pista. Mide lo difícil que se lo puso al sacador para ganar el punto gratis.")}`;
}

/* ---- ensamblar el bloque profundo dentro de la ficha ---- */
function bloqueProfundo(p,dp){
 const w=document.createElement("div");w.className="deep";
 w.innerHTML=`<div class="deep-cab"><span class="deep-sello">ANÁLISIS PROFUNDO</span>
   <span class="deep-txt">Este partido se anotó golpe a golpe. Todo lo de este bloque son recuentos de lo que pasó en la pista, punto por punto.</span></div>
  <div id="dpTv"></div>
  ${recuentos(p,dp)}
  ${nuevasVars(p,(PROF[p.k]||{}).nv)}
  ${armaGrieta(p,dp)}
  <div class="colt">corto o largo <button class="ast" data-ex="Qué porcentaje de puntos ganó cada uno según cuántos golpes duró el intercambio. Debajo de cada punto, cuántos puntos de esa longitud se jugaron. Con menos de tres, no se dibuja." aria-label="Qué significa">*</button></div>
  <div class="vbox"><canvas id="dpRally"></canvas></div>
  <div class="colt">adónde sacó <button class="ast" data-ex="La pista vista desde arriba. Cada zona se ilumina según qué proporción de sus primeros saques mandó ahí: abierto, al cuerpo o a la T, en el lado de iguales y en el de ventaja." aria-label="Qué significa">*</button></div>
  <div class="vbox"><canvas id="dpSaque"></canvas></div>
  <div class="colt">la huella del partido <button class="ast" data-ex="Siete rasgos de cómo jugó cada uno en este partido, convertidos en una silueta. Donde una forma sobresale de la otra, ese jugador fue superior en ese aspecto. Describe este partido, no el estilo habitual del jugador." aria-label="Qué significa">*</button></div>
  <div class="vbox"><canvas id="dpHuella"></canvas></div>`;
 return w;
}


/* ===== RANKING DE PORTADA ===== */
function rankingInit(){
 const R=CUR.rk;if(!R||!E("rkLista"))return;
 const nom=Object.keys(R.puntos),sem=R.semanas,lista=E("rkLista"),sl=E("rkSl");
 sl.min=0;sl.max=sem.length-1;sl.value=sem.length-1;
 lista.style.height=(nom.length*32)+"px";
 const col=["#F0B429","#C9D2DE","#D88B4E"];
 const F={};
 nom.forEach(n=>{const d=document.createElement("div");d.className="rk-f";
  d.innerHTML=`<span class="p"></span><span class="n">${esc(n.split(" ").slice(-1)[0])}</span>
   <div class="b"><i></i></div><span class="v mono"></span>`;
  lista.appendChild(d);F[n]=d});
 const meses=["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
 const pinta=()=>{const i=+sl.value;
  const f=new Date(sem[i]);E("rkSem").textContent=`semana del ${f.getDate()} de ${meses[f.getMonth()]}`;
  const orden=nom.slice().sort((a,b)=>R.puntos[b][i]-R.puntos[a][i]);
  const mx=R.puntos[orden[0]][i]||1;
  orden.forEach((n,k)=>{const d=F[n],pts=R.puntos[n][i],pre=i>0?R.rank[n][i-1]:R.rank[n][i],act=R.rank[n][i];
   d.style.top=(k*32)+"px";
   d.querySelector(".p").textContent=k+1;
   const b=d.querySelector(".b i");b.style.width=(100*pts/mx)+"%";b.style.background=k<3?col[k]:"var(--acc)";b.style.opacity=k<3?1:.55;
   const mov=pre-act;
   d.querySelector(".v").innerHTML=`${pts.toLocaleString("es")}${mov?`<span class="m" style="color:${mov>0?"#2BE38F":"#FF7A45"}">${mov>0?"▲":"▼"}</span>`:""}`});
 };
 let T;
 E("rkPlay").onclick=()=>{clearInterval(T);sl.value=0;pinta();
  T=setInterval(()=>{if(+sl.value>=sem.length-1){clearInterval(T);return}sl.value=+sl.value+1;pinta()},360)};
 sl.oninput=()=>{clearInterval(T);pinta()};
 pinta();
}

/* ===== ARRANQUE ===== */
function cuenta(id,fin){const el=E(id);if(!el)return;const t0=performance.now();
 (function s(){const k=Math.min(1,(performance.now()-t0)/1300),e=1-Math.pow(1-k,4);
  el.textContent=Math.round(fin*e).toLocaleString("es");if(k<1)requestAnimationFrame(s)})()}
(async function(){
 try{await cargarBase();await cargarTemporada(TEMP.actual);CUR={rk:D.rk,semana:D.semana,kpi:D.kpi}}
 catch(e){console.error("[deuce] datos",e);
  document.body.insertAdjacentHTML("afterbegin",'<div style="position:fixed;inset:auto 0 0 0;z-index:300;padding:14px;background:#FF5C39;color:#0B0E14;text-align:center;font-weight:600">No se han podido cargar los datos. Recarga la página en unos segundos.</div>');return}
 E("ult").textContent=fF(CUR.kpi.ultima);
 const s=CUR.semana;
 if(s){E("swNom").textContent=`${s.w} venció a ${s.l}`;E("swSc").textContent=`${s.sc} · ${s.t}`}
 document.querySelectorAll("[data-ir]").forEach(b=>b.onclick=async()=>{
  if(b.dataset.dp){if(ANIO!==String(TEMP.actual))await cambiarTemporada(TEMP.actual,true);
   soloDeep=true;const c=document.querySelector('.ch[data-deep]');if(c)c.setAttribute("aria-pressed","true");
   E("fo").value="es";listos.add("archivo");ir("archivo");filtrar()}
  else ir(b.dataset.ir)});
 document.querySelectorAll(".puerta").forEach(b=>b.onpointermove=e=>{
  const r=b.getBoundingClientRect();
  b.style.setProperty("--mx",(e.clientX-r.left)+"px");b.style.setProperty("--my",(e.clientY-r.top)+"px")});
 document.querySelectorAll("[data-x]").forEach(b=>b.onclick=e=>e.target.closest("dialog").close());
 [E("dM"),E("dP")].forEach(d=>d.addEventListener("click",e=>{if(e.target===d)d.close()}));
 Object.keys(TEMP.anios).sort().reverse().forEach(y=>E("fy").insertAdjacentHTML("beforeend",`<option value="${y}">Temporada ${y}</option>`));
 E("fy").value=ANIO;E("fy").onchange=()=>cambiarTemporada(E("fy").value);
 rellenarFiltros();
 ["q","fs","ft","fr","fo"].forEach(i=>E(i).addEventListener("input",filtrar));
 document.querySelectorAll("#chips .ch").forEach(b=>b.onclick=()=>{
  const on=b.getAttribute("aria-pressed")==="true";b.setAttribute("aria-pressed",String(!on));
  if(b.dataset.todas){todas=!on;["fy","fs","ft","fr"].forEach(i=>E(i).disabled=todas);
   E("q").placeholder=todas?"Busca un jugador o un torneo en las 36 temporadas…":"Busca un jugador, un torneo…"}
  else if(b.dataset.deep)soloDeep=!on;else if(b.dataset.solo)soloRobo=!on;else on?tipos.delete(b.dataset.tp):tipos.add(b.dataset.tp);filtrar()});
 if(window.__EMB){const c=document.querySelector('.ch[data-todas]');if(c)c.hidden=true}
 E("mas").onclick=()=>{tope+=50;todas?buscarTodas(E("q").value.toLowerCase().trim()):pintar()};
 try{pista()}catch(e){console.error("[deuce] pista",e)}
 try{rankingInit()}catch(e){console.error("[deuce] ranking",e)}
 // tooltip del cuadrante
 const box=E("plano"),tip=E("tip");
 const mv=ev=>{const r=box.getBoundingClientRect(),t=ev.touches?ev.touches[0]:ev;
  const mx=t.clientX-r.left,my=t.clientY-r.top;let b=null,bd=1e9;
  pts.forEach(o=>{const dd=(o.px-mx)**2+(o.py-my)**2;if(dd<bd){bd=dd;b=o}});
  if(bd<460&&b){tip.style.opacity=1;tip.style.left=Math.min(mx+16,r.width-265)+"px";tip.style.top=Math.max(8,my-70)+"px";
   tip.innerHTML=`<strong>${esc(b.p.w)}</strong> d. ${esc(b.p.l)}<br><span class="mono" style="font-size:11px;color:var(--muted)">${esc(b.p.sc)} · ${esc(b.p.t)}<br>tensión ${b.p.te} · disputa ${b.p.di}</span>`}
  else tip.style.opacity=0};
 box.addEventListener("pointermove",mv);box.addEventListener("touchstart",mv,{passive:true});
 box.addEventListener("pointerleave",()=>tip.style.opacity=0);
 let tm;addEventListener("resize",()=>{clearTimeout(tm);tm=setTimeout(()=>{if(vistaAct==="lab")montar("lab")},250)});
 document.querySelectorAll("#v-home .rv").forEach(el=>el.classList.add("in"));
 // globo de explicación
 const globo=document.createElement("div");globo.id="globo";document.body.appendChild(globo);
 const muestra=(el)=>{const ex=el.dataset.ex;if(!ex)return;
  // un <dialog> modal vive en la capa superior del navegador: el globo tiene
  // que estar DENTRO de él o quedará pintado por debajo, invisible
  const capa=el.closest("dialog[open]")||document.body;
  if(globo.parentNode!==capa)capa.appendChild(globo);
  globo.textContent=ex;globo.classList.add("on");
  const r=el.getBoundingClientRect();
  const w=Math.min(330,innerWidth-24);globo.style.maxWidth=w+"px";
  let x=r.left+r.width/2-w/2;x=Math.max(12,Math.min(innerWidth-w-12,x));
  globo.style.left=x+"px";
  const alto=globo.offsetHeight||120;
  globo.style.top=(r.top-alto-10>8?r.top-alto-10:r.bottom+10)+"px"};
 const oculta=()=>globo.classList.remove("on");
 document.addEventListener("pointerover",e=>{const a=e.target.closest(".ast");a?muestra(a):oculta()});
 document.addEventListener("focusin",e=>{const a=e.target.closest(".ast");if(a)muestra(a)});
 document.addEventListener("click",e=>{const a=e.target.closest(".ast");
  if(a){e.preventDefault();e.stopPropagation();muestra(a)}else oculta()},true);
 addEventListener("scroll",oculta,{passive:true});
 document.querySelectorAll(".panel").forEach(p=>p.addEventListener("scroll",oculta,{passive:true}));
})();
