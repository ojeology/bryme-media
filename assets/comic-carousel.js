/* BRYME Match Comic — multi-match engine. data-comic on #mc-hero picks the match.
   Images + single caption track the AUDIO progress. One caption at a time. */
(function(){
  var AUDIO_DIR="/assets/audio/comic/";
  var MATCHES={
    "hull-united":{
      dir:"/assets/img/sports/comics/hull-united-mw1/",
      home:{ab:"HUL",sw:"sw-amber",clr:"#f5a300"},away:{ab:"UTD",sw:"sw-red",clr:"#e23b3b"},
      chapters:[
        {imgs:["01.jpg","19.jpg"],audio:"hu-ch01.mp3",tag:"Homecoming",min:"PRE-MATCH",h:0,a:0,st:"build",title:"9 years done — Tigers return!",
         cap:[["🎙️ Commentator","Nine years for relegation jail don end! Hull enter Premier League like person wey collect alert! MKM dey burst!","c"],["Hull fan","Omo! I don wait nine years for this night. My heart dey beat!","f"]]},
        {imgs:["13.jpg","20.jpg","02.jpg","14.jpg","15.jpg"],audio:"hu-ch02.mp3",tag:"1' · Kick-off",min:"1'",h:0,a:0,st:"live",title:"Whistle blow — Hull press!",
         cap:[["🎙️ Commentator","Teams dey tunnel, eye dey red! Whistle blow — Hull press like say dem no get brake!","c"],["Hull player","We no go give dem breathing space! Press, press, press!","h"],["United player","These boys dey run like say dem drink fuel! Calm down na!","u"]]},
        {imgs:["03.jpg","21.jpg"],audio:"hu-ch03.mp3",tag:"12' · Save",min:"12'",h:0,a:0,st:"live",title:"Tzolakis catch am like rent!",
         cap:[["🎙️ Commentator","Tzolakis catch ball like landlord wey come collect house rent! E be like say he get three hands!","c"],["Tzolakis","Welcome to Hull, my brother. Carry your ball go front!","h"]]},
        {imgs:["04.jpg","05.jpg","06.jpg","22.jpg"],audio:"hu-ch04.mp3",tag:"17' · GOAL",min:"17'",h:1,a:0,st:"live",title:"Corner → header → AJAYI goal!",
         cap:[["🎙️ Commentator","Corner kick — setup dey load! McBurnie head am… saved! But Ajayi pounce on the rebound — GOOOAL!","c"],["Ajayi","Scatter the net! Dem think say we come here to play!","h"],["United defender","Wait, wetin just happen? We wey suppose control game?","u"]]},
        {imgs:["07.jpg","24.jpg"],audio:"hu-ch05.mp3",tag:"1–0 · Scene",min:"17'",h:1,a:0,st:"live",title:"MKM don turn mad house!",
         cap:[["🎙️ Commentator","MKM Stadium don turn mad house! Nine years of waiting, e don pay!","c"],["Ajayi","I don wait my whole career for this kind night. E choke!","h"]]},
        {imgs:["16.jpg","23.jpg","08.jpg"],audio:"hu-ch06.mp3",tag:"34' · Bruno hot",min:"34'",h:1,a:0,st:"live",title:"Bruno dey blame everybody!",
         cap:[["🎙️ Commentator","Bruno don dey hot! He dey blame referee, ball, even the wind! Then Dorgu see yellow!","c"],["Bruno Fernandes","Wetin be this?! Nobody dey mark!","u"],["Referee","Na card be that. No begging, my friend.","r"]]},
        {imgs:["09.jpg","10.jpg","24.jpg"],audio:"hu-ch07.mp3",tag:"38' · GOAL",min:"38'",h:2,a:0,st:"live",title:"Free kick → MENDY header! 2–0!",
         cap:[["🎙️ Commentator","Free kick — danger dey load! Mendy rise like helicopter for set-piece — two nil o!","c"],["Mendy","Fly high! Another set piece chop una clean!","h"],["Bruno Fernandes","How we con leave tall man for free header again?!","u"]]},
        {imgs:["11.jpg","17.jpg"],audio:"hu-ch08.mp3",tag:"60' · Possession",min:"60'",h:2,a:0,st:"live",title:"72% award vs 3 points",
         cap:[["🎙️ Commentator","United get 72% possession award, but Hull fans dey count their 3 points! Wall no dey move!","c"],["United player","Omo, we get 72% possession o! We dey dictate!","u"],["Hull defender","Sorry say possession no dey inside soup. 2-0 remains 2-0!","h"]]},
        {imgs:["18.jpg","25.jpg"],audio:"hu-ch09.mp3",tag:"78' · Double save",min:"78'",h:2,a:0,st:"live",title:"Tzolakis wall no dey break!",
         cap:[["🎙️ Commentator","Tzolakis don do double save o! First the shot, then the rebound! Wall no dey break!","c"],["Tzolakis","Anything wey enter my box, I go commot!","h"],["Sesko","This keeper dey impossible! Wetin man go do?!","u"]]},
        {imgs:["12.jpg","26.jpg"],audio:"hu-ch10.mp3",tag:"Full time",min:"FT",h:2,a:0,st:"ft",title:"Red Devils? Crying Devils!",
         cap:[["🎙️ Commentator","Full time! Red Devils? Crying Devils proper! Tigers are back — and we starving!","c"],["Rashford","We come all this way only to chop premium tears.","u"],["Hull captain","Go tell them say the Tigers are back!","h"]]}
      ]
    },
    "arsenal-coventry":{
      dir:"/assets/img/sports/comics/arsenal-coventry-mw1/",
      home:{ab:"ARS",sw:"sw-red",clr:"#d11"},away:{ab:"COV",sw:"sw-sky",clr:"#5aa9e6"},
      chapters:[
        {imgs:["ac-01.jpg","ac-09.jpg","ac-10.jpg","ac-19.jpg"],audio:"ac-ch01.mp3",tag:"Homecoming",min:"PRE-MATCH",h:0,a:0,st:"build",title:"Champions open the defence!",
         cap:[["🎙️ Commentator","Champions Arsenal open the defence tonight! Twenty-two years of waiting don end — now dem dey guard the crown!","c"],["Arsenal fan","We be champions! Anybody wey enter Emirates go collect!","hm"],["Coventry fan","We just come back o. Make dem no use us do birthday party!","aw"]]},
        {imgs:["ac-02.jpg","ac-11.jpg","ac-20.jpg"],audio:"ac-ch02.mp3",tag:"1' · In control",min:"1'",h:0,a:0,st:"live",title:"Arsenal dey toy with dem!",
         cap:[["🎙️ Commentator","Whistle blow! Arsenal dey move the ball like training — Coventry no even smell am!","c"],["Arsenal midfielder","Calm, calm, make dem chase shadow!","hm"],["Coventry defender","Haaa, the ball dey fly up and down! I don already tire!","aw"]]},
        {imgs:["ac-03.jpg","ac-12.jpg","ac-13.jpg","ac-21.jpg"],audio:"ac-ch03.mp3",tag:"GOAL · 12'",min:"12'",h:1,a:0,st:"live",title:"Opener! Arsenal 1–0!",
         cap:[["🎙️ Commentator","GOOOAL! The ball don enter! Champions don open account — Arsenal one nil!","c"],["Arsenal fan","E choke! First one don enter!","hm"],["Coventry keeper","I suppose catch that one... the boy hit am well!","aw"]]},
        {imgs:["ac-04.jpg","ac-14.jpg","ac-22.jpg"],audio:"ac-ch04.mp3",tag:"25' · Big save",min:"25'",h:1,a:0,st:"live",title:"Coventry try, keeper say no!",
         cap:[["🎙️ Commentator","Coventry try counter! But Arsenal keeper say not today — big save!","c"],["Arsenal keeper","You think say e go enter? No be today!","hm"],["Coventry fan","Ah! We for score that one o!","aw"]]},
        {imgs:["ac-05.jpg","ac-15.jpg","ac-23.jpg"],audio:"ac-ch05.mp3",tag:"GOAL · 40'",min:"40'",h:2,a:0,st:"live",title:"Two nil — defense scatter!",
         cap:[["🎙️ Commentator","Two nil! Another one don enter! Coventry defense dey scatter like pack of cards!","c"],["Arsenal fan","Two! Make we chop more!","hm"],["Coventry defender","Wetin be this?! Dem no dey tire?","aw"]]},
        {imgs:["ac-06.jpg","ac-16.jpg","ac-24.jpg"],audio:"ac-ch06.mp3",tag:"55' · Frustration",min:"55'",h:2,a:0,st:"live",title:"Coventry dey find miracle!",
         cap:[["🎙️ Commentator","Coventry boys dey look themselves — 'we go come back from this one?'","c"],["Coventry fan","Bros, na only 2-0. Miracle dey happen... sometimes!","aw"],["Arsenal fan","Miracle kee you there! Na 3 we dey look for!","hm"]]},
        {imgs:["ac-07.jpg","ac-17.jpg","ac-25.jpg"],audio:"ac-ch07.mp3",tag:"GOAL · 75'",min:"75'",h:3,a:0,st:"live",title:"Three nil — rout confirmed!",
         cap:[["🎙️ Commentator","THREE NIL! Rout confirmed! Champions dey show say last season no be luck!","c"],["Arsenal fan","Three! Statement of intent! The crown dey stay!","hm"],["Coventry fan","Abeg, referee blow make we go house!","aw"]]},
        {imgs:["ac-08.jpg","ac-18.jpg","ac-26.jpg"],audio:"ac-ch08.mp3",tag:"Full time",min:"FT",h:3,a:0,st:"ft",title:"Clean sheet — defence starts well!",
         cap:[["🎙️ Commentator","Full time! Arsenal three, Coventry nil — clean sheet, three points, defence don start well!","c"],["Arsenal fan","Champions! Same again next week!","hm"],["Coventry fan","Long season dey front... we go re-group!","aw"]]}
      ]
    },
    "brentford-tottenham":{
      dir:"/assets/img/sports/comics/brentford-tottenham-mw1/",
      home:{ab:"BRE",sw:"sw-rwstripes",clr:"#e23b3b"},away:{ab:"TOT",sw:"sw-white",clr:"#e6e8ec"},
      chapters:[
        {imgs:["bc-01.jpg","bc-09.jpg","bc-10.jpg","bc-24.jpg"],audio:"bc-ch01.mp3",tag:"Derby night",min:"PRE-MATCH",h:0,a:0,st:"build",title:"London derby — who go cry?",
         cap:[["🎙️ Commentator","London derby night for west London! Brentford dey buzz, Spurs dey carry big-boy name come — make we see who go cry!","c"],["Brentford fan","Na we be the real Bees! Any London team wey come here go collect!","hm"],["Spurs fan","Abeg, na pre-season form dem dey use. We go show dem today!","aw"]]},
        {imgs:["bc-02.jpg","bc-11.jpg","bc-12.jpg","bc-25.jpg"],audio:"bc-ch02.mp3",tag:"GOAL · 12'",min:"12'",h:1,a:0,st:"live",title:"Lewis-Potter sting dem early!",
         cap:[["🎙️ Commentator","GOOOAL! Lewis-Potter don sting dem early! Brentford one nil — Spurs never even settle!","c"],["Lewis-Potter","Open am sharp-sharp! Dem think say na play!","hm"],["Spurs defender","Wait, match don start? Who mark am?!","aw"]]},
        {imgs:["bc-03.jpg","bc-13.jpg","bc-21.jpg"],audio:"bc-ch03.mp3",tag:"Press",min:"20'",h:1,a:0,st:"live",title:"Brentford press like debt!",
         cap:[["🎙️ Commentator","Brentford dey press dem like say dem owe dem money! Spurs no fit breathe!","c"],["Brentford player","High press, no rest! Make dem fear!","hm"],["Spurs player","Haaa, these boys dey run two engine!","aw"]]},
        {imgs:["bc-04.jpg","bc-14.jpg","bc-15.jpg"],audio:"bc-ch04.mp3",tag:"GOAL · 33'",min:"33'",h:2,a:0,st:"live",title:"Janelt! Two nil — defense na sieve!",
         cap:[["🎙️ Commentator","Two nil! Janelt add another one! Spurs defense don turn to sieve!","c"],["Janelt","Two don enter! The bees dey sting steady!","hm"],["Spurs fan","This one na film trick! How we con dey lose like this?!","aw"]]},
        {imgs:["bc-05.jpg","bc-16.jpg","bc-22.jpg"],audio:"bc-ch05.mp3",tag:"Frustration",min:"40'",h:2,a:0,st:"live",title:"Spurs dey look themselves!",
         cap:[["🎙️ Commentator","Spurs boys dey look themselves — 'we go come back from this one?' E hard o!","c"],["Spurs player","Make we just try score one, abeg!","aw"],["Brentford fan","Score one kee una! Na three we dey look for!","hm"]]},
        {imgs:["bc-06.jpg","bc-17.jpg","bc-18.jpg"],audio:"bc-ch06.mp3",tag:"GOAL · 48'",min:"48'",h:3,a:0,st:"live",title:"Kayode! Three nil — rout proper!",
         cap:[["🎙️ Commentator","THREE NIL! Kayode finish the wahala just after half! Rout proper!","c"],["Kayode","Game over! The bees don take over London tonight!","hm"],["Spurs fan","Referee, abeg blow make we go house!","aw"]]},
        {imgs:["bc-07.jpg","bc-19.jpg","bc-23.jpg"],audio:"bc-ch07.mp3",tag:"Silent away end",min:"80'",h:3,a:0,st:"live",title:"Away end quiet like cemetery!",
         cap:[["🎙️ Commentator","The away end don quiet like cemetery. Only the home end dey make noise!","c"],["Spurs fan","I no fit shout again. Make we just go home.","aw"],["Brentford fan","Sing louder, na your town we dey!","hm"]]},
        {imgs:["bc-08.jpg","bc-20.jpg","bc-26.jpg"],audio:"bc-ch08.mp3",tag:"Full time",min:"FT",h:3,a:0,st:"ft",title:"West London na Bees own!",
         cap:[["🎙️ Commentator","Full time! Brentford three, Tottenham nil! The Bees don show say west London na their own!","c"],["Brentford fan","London is red-and-white tonight! Champions of the derby!","hm"],["Spurs fan","Long journey back across London... silent coach!","aw"]]}
      ]
    },
    "real-espanyol":{
      dir:"/assets/img/sports/comics/real-espanyol-mw1/",
      home:{ab:"ESP",sw:"sw-blue",clr:"#1c6ac4"},away:{ab:"RMA",sw:"sw-white",clr:"#e6e8ec"},
      chapters:[
        {imgs:["re-01.jpg","re-09.jpg","re-10.jpg","re-19.jpg"],audio:"re-ch01.mp3",tag:"Barcelona night",min:"PRE-MATCH",h:0,a:0,st:"build",title:"Underdogs dey host the kings!",
         cap:[["🎙️ Commentator","Barcelona night! Espanyol dey host the big boys Real Madrid — can the underdogs cause wahala?","c"],["Espanyol fan","Make dem come! Today we go show say Barcelona no be only one team!","hm"],["Real Madrid fan","Na three points we carry come. No slip-up!","aw"]]},
        {imgs:["re-02.jpg","re-11.jpg","re-20.jpg"],audio:"re-ch02.mp3",tag:"GOAL · Real lead",min:"14'",h:0,a:1,st:"live",title:"Real open scoring — class show!",
         cap:[["🎙️ Commentator","Real Madrid don open scoring! Class show — the kings lead!","c"],["Real Madrid fan","As expected! Na we be the kings!","aw"],["Espanyol defender","E never finish! We go fight back!","hm"]]},
        {imgs:["re-03.jpg","re-12.jpg","re-21.jpg"],audio:"re-ch03.mp3",tag:"GOAL · 30'",min:"30'",h:1,a:1,st:"live",title:"CALA! Equalizer — underdogs dey bite!",
         cap:[["🎙️ Commentator","CALA! Equalizer! Espanyol don level — one all! The underdogs dey bite!","c"],["Cala","I don level am! Make dem know say we dey here!","hm"],["Real Madrid fan","Wetin?! How dis one happen?!","aw"]]},
        {imgs:["re-04.jpg","re-13.jpg","re-22.jpg"],audio:"re-ch04.mp3",tag:"Barricade",min:"55'",h:1,a:1,st:"live",title:"Espanyol dey defend like say life depend!",
         cap:[["🎙️ Commentator","Espanyol dey defend like say dem life depend on am! Real dey knock but door no dey open!","c"],["Espanyol fan","Hold am! Hold am! Point dey come!","hm"],["Real Madrid player","Why these boys no dey tire?!","aw"]]},
        {imgs:["re-05.jpg","re-14.jpg","re-23.jpg"],audio:"re-ch05.mp3",tag:"Real dey fume",min:"75'",h:1,a:1,st:"live",title:"Time dey go — score dey stay one-all!",
         cap:[["🎙️ Commentator","Real Madrid dey fume! Time dey go, score dey stay one-all!","c"],["Real Madrid fan","Omo, we go drop points like this?!","aw"],["Espanyol fan","Sing! The kings dey sweat!","hm"]]},
        {imgs:["re-06.jpg","re-15.jpg","re-16.jpg","re-24.jpg"],audio:"re-ch06.mp3",tag:"GOAL · 90'",min:"90'",h:1,a:2,st:"live",title:"CARLOS ESPÍ! Stolen at the death!",
         cap:[["🎙️ Commentator","GOOOAL! CARLOS ESPÍ! Ninety minutes! Real Madrid don steal am for the death — two-one!","c"],["Carlos Espí","Now! Now I score! That na why I dey here!","aw"],["Espanyol fan","No no no! Not like this! We were winning!","hm"]]},
        {imgs:["re-07.jpg","re-17.jpg","re-25.jpg"],audio:"re-ch07.mp3",tag:"Heartbreak",min:"90+2'",h:1,a:2,st:"live",title:"Espanyol dey cry — football cruel!",
         cap:[["🎙️ Commentator","Espanyol dey cry! Dem hold Real for 89 minutes, con lose for the last one!","c"],["Espanyol fan","My heart! We were literally just winning! Cruel!","hm"],["Real Madrid fan","Haaa, we escape! Three points na three points!","aw"]]},
        {imgs:["re-08.jpg","re-18.jpg","re-26.jpg"],audio:"re-ch08.mp3",tag:"Full time",min:"FT",h:1,a:2,st:"ft",title:"The kings find a way again!",
         cap:[["🎙️ Commentator","Full time! Espanyol one, Real Madrid two! Stolen at the death — the kings find a way again!","c"],["Real Madrid fan","Champions mentality! We no dey give up!","aw"],["Espanyol fan","Heads up, boys. We play well. Next time!","hm"]]}
      ]
    },
    "mancity-bournemouth":{
      dir:"/assets/img/sports/comics/mancity-bournemouth-mw1/",
      home:{ab:"MCI",sw:"sw-sky",clr:"#5aa9e6"},away:{ab:"BOU",sw:"sw-red",clr:"#e23b3b"},
      chapters:[
        {imgs:["mc-01.jpg","mc-02.jpg","mc-03.jpg","mc-04.jpg"],imgW:[2,2,7,7],audio:"mc-ch01.mp3",tag:"New season",min:"PRE-MATCH",h:0,a:0,st:"build",title:"New season. New manager. New assignment.",
         cap:[["City fan","Omo, new season don start! Boss, today three points o! No excuse today. Make we collect this win.","hm"],["Enzo Maresca","Calm down. We go handle am.","hm"],["City fan","Omo... Bournemouth don land. Na City dem wan play today.","hm"],["Lewis Cook","Everybody dey talk about Manchester City. Make them talk. Focus. We play our football. Let's make them uncomfortable.","aw"]]},
        {imgs:["mc-05.jpg","mc-06.jpg","mc-07.jpg"],imgW:[2,2,3],audio:"mc-ch02.mp3",tag:"AND WE DON START",min:"5'",h:0,a:0,st:"live",title:"And we don start.",
         cap:[["Rúben Dias","Make we start well.","hm"],["Lewis Cook","Make we see. Na only 90 minutes.","aw"],["Elliot Anderson","Move! Move! Go!","hm"],["Djordje Petrović","HOW?! Not today. I dey here.","aw"]]},
        {imgs:["mc-08.jpg","mc-09.jpg","mc-10.jpg"],imgW:[2,2,3],audio:"mc-ch03.mp3",tag:"GOAL · Bournemouth",min:"26'",h:0,a:1,st:"live",title:"Boom. Bournemouth strike first.",
         cap:[["City player","Ah! Almost! Why everybody dey park bus? Una no wan play?","hm"],["James Hill","Na football, boss. We dey play. Na you dey chase us. Clear am!","aw"],["Bournemouth attacker","Don't let him through! Run! Omo, City don open space! Then make we use am!","aw"],["Goalscorer","WE DON SCORE! I tell you! Una see am?!","aw"]]},
        {imgs:["mc-11.jpg","mc-12.jpg","mc-13.jpg","mc-14.jpg"],imgW:[2,2,3,7],audio:"mc-ch04.mp3",tag:"HALF TIME",min:"HT",h:0,a:1,st:"ht",title:"The assist was sweet. The finish was not.",
         cap:[["Elliot Anderson","Omo... how we take concede? Forget am. We go equalize.","hm"],["Phil Foden","Ahhhhh! That was nearly there! NOOOOO! That pass na invitation!","hm"],["Djordje Petrović","Thank you. Nearly no count. Because you miss.","aw"],["City manager","Second half. We change the game.","hm"]]},
        {imgs:["mc-15.jpg","mc-16.jpg"],imgW:[4,2],audio:"mc-ch05.mp3",tag:"The bench",min:"75'",h:0,a:1,st:"live",title:"The game needed something different.",
         cap:[["Enzo Maresca","We need creativity. Go change the game.","hm"],["Rayan Cherki","Give me the ball. Say less.","hm"],["James Hill","Who be this? New problem. Clear am!","aw"],["Phil Foden","Keep pushing! Omo, this goal dey hide!","hm"]]},
        {imgs:["mc-17.jpg","mc-18.jpg","mc-19.jpg"],imgW:[3,3,2],audio:"mc-ch06.mp3",tag:"GOAL · 84'",min:"84'",h:1,a:1,st:"live",title:"84' — equaliser!",
         cap:[["City goalscorer","WE'RE BACK! I TOLD YOU! One more! ONE MORE!","hm"],["Rúben Dias","WE DON COME BACK! Everybody push!","hm"],["James Hill","How we lose this lead? Abeg, just survive!","aw"],["Marco Rose","Fresh legs! Stay focused. Almost no count. Finish the job.","aw"]]},
        {imgs:["mc-20.jpg","mc-21.jpg","mc-22.jpg"],imgW:[3,4,2],audio:"mc-ch07.mp3",tag:"GOAL · 90+1'",min:"90+1'",h:2,a:1,st:"live",title:"90+1' — Gvardiol!!!",
         cap:[["Goalscorer","WE DON WIN AM! LAST MINUTE!","hm"],["Rayan Cherki","NO WAY!","hm"],["Lewis Cook","HOW?! We were winning! Check am well!","aw"],["City player","French boy don cook! Two assists! Omo! Je vous avais dit.","hm"]]},
        {imgs:["mc-23.jpg","mc-24.jpg","mc-25.jpg","mc-26.jpg"],imgW:[2,2,7,4],audio:"mc-ch08.mp3",tag:"Full time",min:"FT",h:2,a:1,st:"ft",title:"Football no get script.",
         cap:[["Lewis Cook","We lead almost the whole game... Football no get pity.","aw"],["Rúben Dias","Three points! Comeback complete!","hm"],["Rayan Cherki","Deux assists. Calmez-vous.","hm"],["City fan","Na why you dey watch football till 90+? Because football fit disgrace you anytime!","hm"]]}
      ]
    },
    "newcastle-liverpool":{
      dir:"/assets/img/sports/comics/newcastle-liverpool-mw1/",
      home:{ab:"NEW",sw:"sw-nwstripes",clr:"#e6e8ec"},away:{ab:"LIV",sw:"sw-red",clr:"#e23b3b"},
      chapters:[
        {imgs:["nl-01.jpg","nl-09.jpg","nl-10.jpg","nl-18.jpg","nl-26.jpg"],audio:"nl-ch01.mp3",tag:"St James' Park",min:"PRE-MATCH",h:0,a:0,st:"build",title:"St James' dey rock!",
         cap:[["\ud83c\udf99\ufe0f Commentator","St James' Park dey rock! Newcastle dey host Liverpool \u2014 two hungry teams!","c"],["Newcastle fan","Magpies for life! We dey ready!","hm"],["Liverpool fan","We go show dem say Anfield no be only place!","aw"]]},
        {imgs:["nl-02.jpg","nl-11.jpg","nl-19.jpg"],audio:"nl-ch02.mp3",tag:"GOAL",min:"22'",h:1,a:0,st:"live",title:"Newcastle score first! One-nil!",
         cap:[["\ud83c\udf99\ufe0f Commentator","GOOOAL! Newcastle don score first! The Magpies dey fly!","c"],["Newcastle fan","E choke! One-nil! How we take score?!","hm"],["Liverpool fan","Wetin?! We suppose score first!","aw"]]},
        {imgs:["nl-03.jpg","nl-12.jpg","nl-20.jpg"],audio:"nl-ch03.mp3",tag:"Under siege",min:"35'",h:1,a:0,st:"live",title:"Liverpool dey press, Toon dey hold!",
         cap:[["\ud83c\udf99\ufe0f Commentator","Liverpool dey press dey press! Newcastle dey hold breath!","c"],["Newcastle player","Hold am! Hold am!","hm"],["Liverpool player","Why these boys no dey tire?!","aw"]]},
        {imgs:["nl-04.jpg","nl-13.jpg","nl-21.jpg"],audio:"nl-ch04.mp3",tag:"GOAL \u00b7 1-1",min:"44'",h:1,a:1,st:"live",title:"Equalizer! Liverpool don level!",
         cap:[["\ud83c\udf99\ufe0f Commentator","Equalizer! Liverpool don level \u2014 one all! E choke!","c"],["Liverpool fan","The Reds don wake up!","aw"],["Newcastle fan","Ah, we suppose hold am small!","hm"]]},
        {imgs:["nl-05.jpg","nl-14.jpg","nl-22.jpg"],audio:"nl-ch05.mp3",tag:"GOAL \u00b7 2-1",min:"63'",h:2,a:1,st:"live",title:"Newcastle score again! Two-one!",
         cap:[["\ud83c\udf99\ufe0f Commentator","NO! Newcastle don score again! Two-one! The Magpies no dey give up!","c"],["Newcastle fan","We lead again! St James' dey burst!","hm"],["Liverpool fan","Not again! How?!","aw"]]},
        {imgs:["nl-06.jpg","nl-15.jpg","nl-23.jpg"],audio:"nl-ch06.mp3",tag:"Onslaught",min:"80'",h:2,a:1,st:"live",title:"Liverpool dey throw everything!",
         cap:[["\ud83c\udf99\ufe0f Commentator","Liverpool dey throw everything forward! Time dey go!","c"],["Liverpool fan","One more! We need one more!","aw"],["Newcastle player","Bros, defend for life!","hm"]]},
        {imgs:["nl-07.jpg","nl-16.jpg","nl-24.jpg"],audio:"nl-ch07.mp3",tag:"GOAL \u00b7 2-2",min:"89'",h:2,a:2,st:"live",title:"EQUALIZER! Two-two! Rescued!",
         cap:[["\ud83c\udf99\ufe0f Commentator","EQUALIZER! Two-two! Liverpool don rescue am! The Reds no dey die!","c"],["Liverpool fan","Yes! We no dey give up!","aw"],["Newcastle fan","Ah, we lose am for the end again!","hm"]]},
        {imgs:["nl-08.jpg","nl-17.jpg","nl-25.jpg"],audio:"nl-ch08.mp3",tag:"Full time",min:"FT",h:2,a:2,st:"ft",title:"Two-two \u2014 proper drama!",
         cap:[["\ud83c\udf99\ufe0f Commentator","Full time! Two-two! Both teams share the points \u2014 proper drama!","c"],["Newcastle fan","Entertaining but painful! One point!","hm"],["Liverpool fan","Character! We fight back!","aw"]]}
      ]
    }
  };
  var PILL={build:"BUILD-UP",live:"LIVE",ht:"HALF TIME",ft:"FULL TIME"};
  var CAP_DUR=16000;
  var MIN_IMG_MS=20000;
  function weightsOf(arr, explicit){
    if(explicit&&explicit.length===arr.length) return explicit;
    return arr.map(function(item){
      var t=typeof item==="string"?item:(item&&item[1])||"";
      return Math.max(1, Math.round(String(t).length/36));
    });
  }
  function pickWeighted(weights, prog){
    var sum=0,i; for(i=0;i<weights.length;i++) sum+=Math.max(0.25,weights[i]);
    var t=prog*sum;
    for(i=0;i<weights.length;i++){ t-=Math.max(0.25,weights[i]); if(t<=0) return i; }
    return weights.length-1;
  }
  function init(){
    var root=document.getElementById("mc-hero"); if(!root) return;
    var slug=root.getAttribute("data-comic")||"hull-united";
    var M=MATCHES[slug]||MATCHES["hull-united"];
    var DIR=M.dir, S=M.chapters, home=M.home, away=M.away;
    /* City–Bournemouth is delivered as 26 independent vertical sideclips.
       Batch 1 has native 9:16 plates and panel audio; later batches fall back
       to their existing plates/tracks until rendered. */
    if(slug==="mancity-bournemouth"){
      var panelText=[
        ["City fan","Omo, new season don start! Boss, today na three points o! No excuse today. Make we collect this win.","hm"],
        ["Lewis Cook","Everybody dey talk about Manchester City. Make them talk. Focus. We play our football.","aw"],
        ["Enzo Maresca","Start fast. Move the ball. Stay patient. Boss, no wahala. Easy work.","hm"],
        ["Marco Rose","Stay compact. Attack when we have space. City get the name. Bournemouth get the plan.","aw"],
        ["Rúben Dias","Make we start well. Na only ninety minutes. Na pitch go decide.","hm"],
        ["Elliot Anderson","Move! Move! Go! Five minutes in and City don already dey knock door.","hm"],
        ["Djordje Petrović","How?! Not today. I dey here. First serious chance and keeper don enter beast mode.","aw"],
        ["James Hill","Clear am! City get the ball. Bournemouth get patience.","aw"],
        ["Bournemouth attacker","Omo, City don open space! Then make we use am! Football no get patience.","aw"],
        ["Marcus Tavernier","WE DON SCORE! Bournemouth strike first. Manchester City nil, Bournemouth one.","aw"],
        ["Rúben Dias","Omo, how we take concede? Forget am. We go equalize.","hm"],
        ["Phil Foden","Ahhhhh! That was nearly there! Nearly no count.","hm"],
        ["Phil Foden","NOOOOO! That pass na invitation! I know!", "hm"],
        ["City manager","Second half. We change the game. City get possession, Bournemouth get the lead.","hm"],
        ["Rayan Cherki","We need creativity? Give me the ball. Say less.","hm"],
        ["City player","Keep pushing! Omo, this goal dey hide! The clock dey run.","hm"],
        ["Marc Guéhi","WE'RE BACK! One more! ONE MORE!", "hm"],
        ["Rúben Dias","WE DON COME BACK! Everybody push! Bournemouth dream win dey slip.","hm"],
        ["Marco Rose","Fresh legs! Stay focused. Almost no count. Finish the job.","aw"],
        ["Joško Gvardiol","WE DON WIN AM! LAST MINUTE! Manchester City two, Bournemouth one.","hm"],
        ["Referee","VAR check. Goal? Goal confirmed. Manchester City two, Bournemouth one.","r"],
        ["City player","French boy don cook! Two assists! Je vous avais dit.","hm"],
        ["Lewis Cook","We lead almost the whole game. Football no get pity.","aw"],
        ["Rúben Dias","Three points! Comeback complete! Full time: Manchester City two, Bournemouth one.","hm"],
        ["Rayan Cherki","Deux assists. Calmez-vous. Victory taste different when na comeback.","hm"],
        ["Narrator","Bournemouth were minutes away from a famous win. Manchester City had other plans. Football no get script.","c"]
      ];
      /* Approximate head anchors for the named speaker in each vertical plate.
         Coordinates are percentages of the 9:16 deck and keep the bubble above
         the character instead of over the action. */
      var bubblePos=[
        [22,48,64],[57,48,60],[35,30,60],[50,32,62],[48,42,62],[52,37,60],[30,34,58],[68,42,58],[53,35,60],
        [42,40,64],[45,42,62],[60,39,60],[55,42,62],[35,31,64],[46,36,60],[57,37,62],[42,40,64],[55,41,64],
        [50,30,62],[43,37,64],[50,30,66],[48,36,64],[59,40,62],[42,42,64],[46,40,64],[50,28,72]
      ];
      var panelCaps=panelText.map(function(c){return [c];});
      function lines(i){panelCaps[i-1]=Array.prototype.slice.call(arguments,1);}
      lines(1,["City fan","Omo, new season don start! Boss, today na three points o!","hm",[22,48,64]],["Enzo Maresca","Calm down. We go handle am.","hm",[35,30,58]]);
      lines(2,["City fan","Omo... Bournemouth don land. Na City dem wan play today.","hm",[24,48,62]],["Lewis Cook","Everybody dey talk about Manchester City. Make them talk.","aw",[58,48,62]],["Marco Rose","Focus. We play our football.","aw",[48,35,60]]);
      lines(3,["Enzo Maresca","Start fast. Move the ball. Stay patient.","hm",[35,30,58]],["Rúben Dias","Boss, no wahala. Easy work.","hm",[54,43,58]]);
      lines(4,["Marco Rose","Stay compact. Attack when we have space.","aw",[50,32,62]],["Adam Smith","Nobody come here to admire the stadium. Maybe three points.","aw",[68,45,58]]);
      lines(5,["Rúben Dias","Make we start well.","hm",[48,42,60]],["Lewis Cook","Make we see. Na only ninety minutes.","aw",[69,44,56]],["City fan","Three points today! Abeg, no stress us.","hm",[22,55,55]]);
      lines(6,["Elliot Anderson","Move! Move! Go!","hm",[52,37,55]],["James Hill","Everybody wake up!","aw",[68,42,52]],["James Hill","I dey awake! Then why you dey watch ball?","aw",[35,43,56]]);
      lines(7,["Erling Haaland","How?!","hm",[48,52,50]],["Djordje Petrović","Not today. I dey here.","aw",[29,33,54]],["City fan","Chai! First serious chance and keeper don enter beast mode.","hm",[23,58,68]]);
      lines(8,["City player","Ah! Almost!","hm",[47,42,56]],["James Hill","Clear am!","aw",[68,40,50]],["Lewis Cook","City get the ball. Bournemouth get patience.","aw",[52,35,62]]);
      lines(9,["James Hill","Don't let him through! Run!","aw",[67,40,54]],["Bournemouth attacker","Omo, City don open space! Then make we use am!","aw",[51,34,60]]);
      lines(10,["Marcus Tavernier","WE DON SCORE!","aw",[43,42,56]],["City defender","How? We were attacking five seconds ago.","hm",[68,48,58]],["City fan","One goal fit still pain you!","hm",[23,57,60]]);
      lines(11,["Rúben Dias","Omo, how we take concede?","hm",[43,43,56]],["Elliot Anderson","Forget am. We go equalize.","hm",[58,40,56]],["Lewis Cook","Na the important part.","aw",[70,42,52]]);
      lines(12,["Phil Foden","Ahhhhh! That was nearly there!","hm",[48,40,58]],["James Hill","Nearly no count.","aw",[66,40,52]],["City fan","Abeg, somebody shoot!","hm",[22,55,58]]);
      lines(13,["Phil Foden","NOOOOO! That pass na invitation!","hm",[50,40,60]],["Djordje Petrović","Thank you.","aw",[30,34,52]],["City fan","Chai! How you miss that one?!","hm",[22,58,58]]);
      lines(14,["City manager","Second half. We change the game.","hm",[34,30,60],"bubbles/mc-14-1.mp3"],["City player","We get the ball, but na dem get the goal.","hm",[55,46,58],"bubbles/mc-14-2.mp3"],["Marco Rose","Don't relax. City will come.","aw",[70,31,58],"bubbles/mc-14-3.mp3"]);
      lines(15,["Enzo Maresca","We need creativity. Go change the game.","hm",[34,32,60]],["Rayan Cherki","Give me the ball. Say less.","hm",[48,43,58]],["James Hill","Who be this? New problem.","aw",[72,45,54]]);
      lines(16,["City player","Keep pushing! This goal dey hide!","hm",[52,37,60]],["Djordje Petrović","Everybody stay focused!","aw",[30,34,54]],["City fan","The clock dey run.","hm",[22,56,54]]);
      lines(17,["Marc Guéhi","WE'RE BACK!","hm",[42,40,58],"bubbles/mc-17-1.mp3"],["Rayan Cherki","I told you! One more!","hm",[57,38,58],"bubbles/mc-17-2.mp3"],["James Hill","How we lose this lead?","aw",[72,44,54]]);
      lines(18,["Rúben Dias","WE DON COME BACK! Everybody push!","hm",[43,42,62]],["James Hill","Abeg, just survive!","aw",[70,44,55]],["Bournemouth fan","Six minutes fit be six years.","aw",[25,58,58]]);
      lines(19,["Marco Rose","Fresh legs! Stay focused!","aw",[50,30,62]],["Outgoing player","Boss, we nearly get am.","aw",[32,45,54]],["Incoming player","Got it.","aw",[68,45,48]]);
      lines(20,["Rayan Cherki","NO WAY!","hm",[57,38,54]],["Gvardiol","WE DON WIN AM! Last minute!","hm",[43,38,58]],["Lewis Cook","HOW?! We were winning!","aw",[70,45,54]]);
      lines(21,["City player","Abeg, make dem no cancel this one.","hm",[42,43,62]],["Referee","Check am well. Goal confirmed.","r",[53,32,58]],["Lewis Cook","Please VAR!","aw",[70,45,52]]);
      lines(22,["City player","French boy don cook! Two assists!","hm",[47,40,60]],["Rayan Cherki","Je vous avais dit.","hm",[58,35,54]],["Enzo Maresca","Na tactical breathing.","hm",[34,30,54]]);
      lines(23,["Lewis Cook","We lead almost the whole game...","aw",[42,44,58]],["Djordje Petrović","One corner, one pass, finish.","aw",[70,42,54]],["Marco Rose","Football no get pity.","aw",[54,31,58]]);
      lines(24,["Rúben Dias","Three points!","hm",[42,42,54]],["Rayan Cherki","Deux assists.","hm",[57,38,54]],["Bournemouth fan","Abeg, make person no talk to me.","aw",[70,46,56]]);
      lines(25,["Enzo Maresca","Anybody wey laugh go train double tomorrow.","hm",[35,30,58]],["City player","Then na everybody!","hm",[54,45,54]],["Rayan Cherki","Calmez-vous. Give me jollof.","hm",[67,47,54]]);
      lines(26,["City fan","Football no get script.","hm",[22,50,58]],["Marco Rose","Bournemouth were minutes away from a famous win.","aw",[68,43,62]],["Narrator","Manchester City had other plans.","c",[50,28,70]]);
      var transcripts=[
        "Omo, new season don start! Boss, today na three points o! No excuse today. Make we collect this win. Calm down. We go handle am. New season. New manager. New assignment.",
        "Omo, Bournemouth don land. Na City dem wan play today. Everybody dey talk about Manchester City. Make them talk. Focus. We play our football. Bournemouth no come sightseeing.",
        "Start fast. Move the ball. Stay patient. Boss, no wahala. Easy work. Omo, everybody too confident today. Abeg, just score early. I no wan suffer. Inside the dressing room, confidence dey full ground... at least, for now.",
        "Stay compact. Attack when we have space. Manchester City? Yes. Good. Nobody come here to admire the stadium. Omo, if we fit score first, this place go quiet. Focus. City get the name. Bournemouth get the plan.",
        "Make we start well. Make we see. Na only ninety minutes. Three points today! Abeg, no stress us. And we don start. Matchday one. Manchester City versus Bournemouth. Na pitch go decide.",
        "Move! Move! Go! Not today. Everybody wake up! I dey awake! Then why you dey watch ball? Na tactical observation. Five minutes in and City don already dey knock door.",
        "How?! Not today. I dey here. Keeper! I dey here. Chai! First serious chance and Bournemouth keeper don already enter beast mode.",
        "Ah! Almost! Clear am! Why everybody dey park bus? Na football, boss. We dey play. Na you dey chase us. City get the ball. Bournemouth get patience.",
        "Don't let him through! Run! Omo, City don open space! Then make we use am! Abeg, slow down! I dey beg you! One second City dey attack. Next second dem dey defend. Football no get patience.",
        "We don score! Tavernier finishes the counter! Manchester City nil, Bournemouth one. Calm down. Na one goal, but one goal fit still pain you.",
        "Omo, how we take concede? Forget am, we go equalize. Dem get one chance and dem use am. Possession na City, goal na Bournemouth. Football get sense of humour.",
        "Ahhhhh, that was nearly there! Nearly no count. City don change gear, but Bournemouth say no problem, we go defend.",
        "Nooooo! That pass na invitation! I know! Thank you, says the keeper. The assist was sweet. The finish was not. Manchester City still nil, Bournemouth one.",
        "Half-time. Bournemouth one, Manchester City nil. Boss, we get the ball, but na dem get the goal. Second half, we change the game. Bournemouth, do not relax. City will come.",
        "We need creativity. Give me the ball. Say less. Omo, na this guy we dey wait for. Bournemouth defenders ask, who be this? New problem.",
        "Keep pushing! Clear am! Everybody stay focused! Omo, this goal dey hide. The clock dey run, Bournemouth still holding on.",
        "Corner delivered. Guéhi powers home the header! We are back! I told you! Manchester City one, Bournemouth one. One more! One more!",
        "We don come back! One more! Everybody push! Cherki don enter the game, and now he don create the equaliser. Bournemouth dream win dey slip.",
        "Eighty-eight minutes. Fresh legs, stay focused! Boss, we nearly get am. Almost no count. City don wake up. Make this game just finish.",
        "Ninety-one minutes! Gvardiol finishes low into the corner! We don win am! Last minute! Bournemouth were winning, but Manchester City turn am around. The comeback is complete.",
        "Abeg, make dem no cancel this one. VAR check. Goal? Goal confirmed! Manchester City two, Bournemouth one. Football no get pity today.",
        "French boy don cook! Two assists! Je vous avais dit. Wetin he talk again? Forget am, just celebrate! Boss, you nearly collapse. Na tactical breathing.",
        "We lead almost the whole game. Football no get pity. One corner, one pass, finish. Sometimes football fit turn sweet dream to premium breakfast in two minutes.",
        "Full time! Manchester City two, Bournemouth one. Three points! Comeback complete! Na why we never leave stadium. Football fit disgrace you anytime.",
        "Boss don talk say we go win! Everybody laugh. Anybody wey laugh go train double tomorrow. Then na everybody! Calmez-vous. Give the French professor jollof, e don deserve am.",
        "Football no get script. Bournemouth were minutes away from a famous win. Manchester City had other plans. Bournemouth lead, City comeback, last-minute heartbreak. BRYME Football Comics.",
        "One nil down and una still dey pass the ball! Boss, abeg wake up! Maresca, this your calm calm football dey give us hypertension! Bournemouth get one chance and dem use am. City fans, no panic? No panic ke!",
        "Maresca! We roast you when we were one nil down, but you don change the game! Omo, comeback complete! Manchester City two, Bournemouth one! I tell una say we go win! Na why you watch football till ninety plus!",
        "If you enjoy this comeback, please like, follow and share! More BRYME Football Comics dey come. Football no get script, but you fit help this story reach your people."
      ];
      var flat=[], pi=0;
      M.chapters.forEach(function(ch){ch.imgs.forEach(function(img){
        pi++; var n=("0"+pi).slice(-2);
        flat.push({imgs:[pi<=26?"vertical/mc-"+n+".jpg":img],audio:pi<=26?"panels/mc-"+n+".mp3":ch.audio,
          tag:pi===1?"New season":pi===10?"GOAL · 26'":pi===17?"GOAL · 84'":pi===20?"GOAL · 90+1'":pi===24?"Full time":ch.tag,
          min:pi===1?"PRE-MATCH":pi===10?"26'":pi===17?"84'":pi===20?"90+1'":pi>=24?"FT":ch.min,
          h:pi<10?0:pi<17?0:pi<20?1:2,a:pi<10?0:pi<20?1:1,st:pi>=24?"ft":pi===1?"build":"live",
          scorer:pi===10?"Tavernier":pi===17?"Guéhi":pi===20?"Gvardiol":"",bubblePos:bubblePos[pi-1],
          title:pi===1?"New season. New manager. New assignment.":pi===10?"Boom. Tavernier scores first.":pi===17?"84' — Guéhi equaliser!":pi===20?"90+1' — Gvardiol winner!":pi===26?"Manchester City 2–1 Bournemouth · Tavernier 26' · Guéhi 84' · Gvardiol 90+1'":ch.title,
          cap:panelCaps[pi-1],transcript:transcripts[pi-1]});
      });});
      flat.push({imgs:["vertical/mc-27.jpg"],audio:"panels/mc-27.mp3",tag:"Fan reaction",min:"0–1",h:0,a:1,st:"live",title:"One goal down and the fans don vex!",bubblePos:[36,38,68],cap:[["City fan","Maresca, abeg wake up! This calm calm football dey give us hypertension!","hm",[36,38,68],"bubbles/mc-27-1.mp3"],["City fan","No panic ke? No panic!","hm",[22,52,58],"bubbles/mc-27-2.mp3"]],transcript:transcripts[26]});
      flat.push({imgs:["vertical/mc-28.jpg"],audio:"panels/mc-28.mp3",tag:"Comeback complete",min:"FT",h:2,a:1,st:"ft",title:"The same fans don turn celebration committee!",bubblePos:[35,38,68],cap:[["City fan","Maresca, we roast you when we were one nil down!","hm",[22,52,62],"bubbles/mc-28-1.mp3"],["City fan","Omo, comeback complete! Manchester City two, Bournemouth one!","hm",[44,39,68],"bubbles/mc-28-2.mp3"]],transcript:transcripts[27]});
      flat.push({imgs:["vertical/mc-29.jpg"],audio:"panels/mc-29.mp3",tag:"BRYME Football Comics",min:"END",h:2,a:1,st:"ft",title:"Please like, follow and share.",bubblePos:[50,32,76],cap:[["BRYME","Please like, follow and share! More BRYME Football Comics dey come.","c",[50,32,76],"bubbles/mc-29-1.mp3"]],transcript:transcripts[28]});
      var halftimeFan=flat.splice(26,1)[0];
      flat.splice(14,0,halftimeFan);
      S=flat;
    }
    root.className="mc"+(slug==="mancity-bournemouth"?" mc-vertical":"");
    root.style.setProperty("--home-c",home.clr);
    root.style.setProperty("--away-c",away.clr);
    root.innerHTML=
      '<div class="mc-deck">'+
        '<div class="mc-bars" aria-hidden="true"></div>'+
        '<div class="mc-track"></div>'+
        '<div class="mc-hud"><span class="mc-pill" id="mcpill"></span><span class="mc-score" id="mcscore"></span></div>'+
        '<div class="mc-mark"><b>BRYME</b><span>@bryme</span></div>'+
        '<div class="mc-bubble-slot"><div class="mc-bubble" id="mcbubble"></div></div>'+
        '<div class="mc-cap-slot"><div class="mc-cap-card" id="mccap"></div></div>'+
      '</div>'+
      '<div class="mc-head"><span class="mc-tag" id="mctag"></span><h2 id="mctitle"></h2></div>'+
      '<div class="mc-ctrl">'+
        '<button class="mc-nav mc-prev" aria-label="Previous">‹ Prev</button>'+
        '<div class="mc-dots"></div>'+
        '<button class="mc-play" aria-pressed="true">⏸ Pause</button>'+
        '<button class="mc-sound" aria-pressed="false">🔇 Sound</button>'+
        '<button class="mc-fs-open" aria-label="Vertical TikTok view">📱 TikTok</button>'+
        '<button class="mc-nav mc-next" aria-label="Next">Next ›</button>'+
        '<span class="mc-cnt" id="mccnt"></span>'+
      '</div>'+
      '<div class="mc-md">'+
        '<span class="mc-md-i on"><span class="mc-md-n">● Matchday 1</span><span class="mc-md-s">BRYME Match Comic · playing now</span></span>'+
        '<a class="mc-md-i soon" href="/sports/premier-league/"><span class="lock">🔒</span><span class="mc-md-n">Matchday 2</span><span class="mc-md-s">Comic drops after full time</span></a>'+
        '<a class="mc-md-i soon" href="/sports/premier-league/"><span class="lock">🔒</span><span class="mc-md-n">Matchday 3</span><span class="mc-md-s">Coming soon</span></a>'+
      '</div>'+
      '<button class="mc-fs-close" id="mcfsx" aria-label="Exit vertical view">✕</button>';
    var track=root.querySelector(".mc-track"),dotsEl=root.querySelector(".mc-dots"),barsEl=root.querySelector(".mc-bars"),
        pill=root.querySelector("#mcpill"),score=root.querySelector("#mcscore"),tag=root.querySelector("#mctag"),
        title=root.querySelector("#mctitle"),cntEl=root.querySelector("#mccnt"),playBtn=root.querySelector(".mc-play"),
        soundBtn=root.querySelector(".mc-sound"),deck=root.querySelector(".mc-deck"),capCard=root.querySelector("#mccap"),bubble=root.querySelector("#mcbubble"),bubbleSlot=root.querySelector(".mc-bubble-slot"),fsBtn=root.querySelector(".mc-fs-open"),fsx=root.querySelector(".mc-fs-close"),len=S.length;
    track.innerHTML=S.map(function(s,i){
      var layers=s.imgs.map(function(g,k){return '<img class="mc-layer'+(k===0?' on':'')+'" src="'+DIR+g+'" alt="Original BRYME comic frame: '+s.title+'" loading="'+(i||k?'lazy':'eager')+'">';}).join("");
      return '<div class="mc-card">'+layers+'</div>';
    }).join("");
    dotsEl.innerHTML=S.map(function(s,i){return '<button type="button" aria-label="Chapter '+(i+1)+'"></button>';}).join("");
    barsEl.innerHTML=S.map(function(){return '<i><span></span></i>';}).join("");
    var cards=[].slice.call(track.children);
    var dots=[].slice.call(dotsEl.children);
    var bars=[].slice.call(barsEl.children).map(function(b){return b.firstChild;});
    dots.forEach(function(b,i){b.addEventListener("click",function(){show(i,i>idx?"next":"prev");});});

    var audio=document.createElement("audio"); audio.preload="auto"; audio.setAttribute("aria-hidden","true"); root.appendChild(audio);
    var bubbleAudio=document.createElement("audio"); bubbleAudio.preload="auto"; bubbleAudio.setAttribute("aria-hidden","true"); root.appendChild(bubbleAudio);
    var muted=true, audioOK=true;
    bubbleAudio.addEventListener("ended",function(){
      var ch=S[idx];
      if(playing&&ch.cap[curCap+1]&&ch.cap[curCap+1][4]){ curCap++; showCap(ch.cap[curCap]); }
      else hideSpeech();
    });
    var audioEnded=false;
    audio.addEventListener("ended",function(){
      audioEnded=true;
      if(playing&&!hover) show(idx+1,"next");
    });
    audio.addEventListener("error",function(){ audioOK=false; });
    function loadAudio(i){ var s=S[i]; if(s.audio){ audioOK=true; audio.src=AUDIO_DIR+s.audio; audio.load(); } }
    function playAudio(){ if(!muted&&S[idx].audio&&!S[idx].cap.some(function(c){return c[4];})){ audio.currentTime=0; var p=audio.play(); if(p&&p.catch)p.catch(function(){audioOK=false;}); } }
    function stopAudio(){ try{audio.pause();}catch(e){} }
    function setLayer(card,li){ var ls=card.querySelectorAll(".mc-layer"); ls.forEach(function(l,k){l.classList.toggle("on",k===li);}); }
    var capTimer=null,bubbleTimer=null;
    function hideSpeech(){ bubble.classList.remove("in"); capCard.classList.remove("in"); }
    function showCap(c){
      if(capTimer)clearTimeout(capTimer); if(bubbleTimer)clearTimeout(bubbleTimer);
      hideSpeech();
      capTimer=setTimeout(function(){
        capCard.className="mc-cap-card "+c[2];
        capCard.innerHTML='<i>'+c[0]+'</i><b></b>';
        var bp=c[3]||S[idx].bubblePos||[50,36,70];
        bubbleSlot.style.left=bp[0]+"%"; bubbleSlot.style.top=bp[1]+"%"; bubbleSlot.style.bottom="auto"; bubbleSlot.style.width=bp[2]+"%";
        bubble.className="mc-bubble "+c[2];
        bubble.innerHTML='<b>'+c[0]+'</b><span>'+c[1]+'</span>';
        if(c[4]&&!muted){ bubbleAudio.pause(); bubbleAudio.src=AUDIO_DIR+c[4]; bubbleAudio.currentTime=0; var bpPlay=bubbleAudio.play(); if(bpPlay&&bpPlay.catch)bpPlay.catch(function(){}); }
        void capCard.offsetWidth; void bubble.offsetWidth;
        capCard.classList.add("in"); bubble.classList.add("in");
        var speechMs=audio.duration&&isFinite(audio.duration)?audio.duration*1000/Math.max(1,S[idx].cap.length):Math.min(9000,Math.max(4500,durFor(idx)/Math.max(1,S[idx].cap.length)-400));
        bubbleTimer=setTimeout(hideSpeech,Math.max(3000,speechMs));
      },160);
    }

    var idx=0,playing=true,hover=false,elapsed=0,last=0,curLayer=-1,curCap=-1;
    function durFor(i){
      var ch=S[i], iw=ch.imgW||ch.imgs.map(function(){return 1;}), sum=0, n;
      for(n=0;n<iw.length;n++) sum+=iw[n];
      var byImg=sum*MIN_IMG_MS;
      if(slug==="mancity-bournemouth") byImg=Math.max(7000,sum*6000);
      var byCap=ch.cap.length*CAP_DUR+1600;
      return Math.max(byImg, byCap, ch.hold||0);
    }
    function updateHud(){
      var s=S[idx],st=s.st;
      pill.className="mc-pill "+(st==="live"?"live":st==="ft"?"ft":"");
      pill.innerHTML=(st==="live"?'<span class="d"></span>':'')+PILL[st];
      score.innerHTML='<span class="t"><span class="sw '+home.sw+'"></span>'+home.ab+'</span>'+s.h+'–'+s.a+'<span class="t"><span class="sw '+away.sw+'"></span>'+away.ab+'</span><span class="min">'+s.min+'</span>'+(s.scorer?'<span class="scorer">'+s.scorer+'</span>':'');
      tag.textContent=s.tag;title.textContent=s.title;
    }
    function show(n,dir){
      var old=idx;idx=((n%len)+len)%len;var c=cards[idx];
      stopAudio(); bubbleAudio.pause();
      if(old!==idx){var o=cards[old];o.classList.remove("on");o.classList.add(dir==="next"?"left":"right");}
      c.style.transition="none";c.classList.remove("on","left","right");c.classList.add(dir==="next"?"right":"left");
      void c.offsetWidth;c.style.transition="";c.classList.remove("right","left");c.classList.add("on");
      setLayer(c,0);curLayer=0;curCap=-1;capCard.classList.remove("in");
      dots.forEach(function(d,i){d.classList.toggle("on",i===idx);});
      cntEl.textContent=(idx+1)+" / "+len;updateHud();elapsed=0;last=performance.now();audioEnded=false;
      loadAudio(idx); if(!muted) playAudio();
    }
    function loop(now){var dt=now-last;last=now;
      if(playing&&!hover&&(muted||!audioOK)){elapsed+=dt;if(elapsed>=durFor(idx))show(idx+1,"next");}
      if(playing&&!hover&&!muted&&audioOK&&audio.duration&&audio.currentTime>=audio.duration-0.05&&!audioEnded){audioEnded=true;show(idx+1,"next");}
      var ch=S[idx];
      var prog=(!muted&&audioOK&&audio.duration)?(audio.currentTime/audio.duration):Math.min(0.999999,elapsed/durFor(idx));
      prog=Math.max(0,Math.min(0.999999,prog));
      if(ch.imgs.length>1){var li=Math.floor(prog*ch.imgs.length)%ch.imgs.length; if(li!==curLayer){setLayer(cards[idx],li);curLayer=li;}}
      var hasBubbleAudio=ch.cap.some(function(c){return c[4];});
      var ci=Math.floor(prog*ch.cap.length)%ch.cap.length;
      if(!hasBubbleAudio&&ci!==curCap){showCap(ch.cap[ci]);curCap=ci;}
      if(hasBubbleAudio&&curCap<0){curCap=0;showCap(ch.cap[0]);}
      for(var i=0;i<len;i++){bars[i].style.width=(i<idx?100:i===idx?Math.min(100,prog*100):0)+"%";}
      requestAnimationFrame(loop);
    }
    function pause(){if(!playing)return;playing=false;stopAudio();
      playBtn.setAttribute("aria-pressed","false");playBtn.textContent="▶ Play";}
    function resume(){if(playing)return;playing=true;playBtn.setAttribute("aria-pressed","true");playBtn.textContent="⏸ Pause";
      last=performance.now();if(!muted)playAudio();}
    function toggleSound(){
      muted=!muted;soundBtn.setAttribute("aria-pressed",String(!muted));
      soundBtn.textContent=muted?"🔇 Sound":"🔊 Sound on";
      if(muted){stopAudio();}
      else{elapsed=0;last=performance.now();curCap=-1;curLayer=-1;playAudio();}
    }
    root.querySelector(".mc-next").addEventListener("click",function(){show(idx+1,"next");});
    root.querySelector(".mc-prev").addEventListener("click",function(){show(idx-1,"prev");});
    playBtn.addEventListener("click",function(){playing?pause():resume();});
    soundBtn.addEventListener("click",toggleSound);
    function enterFs(){ root.classList.add("mc-fs"); document.body.style.overflow="hidden"; if(muted) toggleSound(); }
    function exitFs(){ root.classList.remove("mc-fs"); document.body.style.overflow=""; }
    fsBtn.addEventListener("click",enterFs);
    fsx.addEventListener("click",exitFs);
    deck.addEventListener("mouseenter",function(){hover=true;});
    deck.addEventListener("mouseleave",function(){hover=false;last=performance.now();if(audioEnded&&playing)show(idx+1,"next");});
    var sx=null;
    deck.addEventListener("touchstart",function(e){sx=e.touches[0].clientX;},{passive:true});
    deck.addEventListener("touchend",function(e){if(sx===null)return;var dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>44)show(dx<0?idx+1:idx-1,dx<0?"next":"prev");sx=null;},{passive:true});
    document.addEventListener("keydown",function(e){if(e.key==="ArrowRight")show(idx+1,"next");else if(e.key==="ArrowLeft")show(idx-1,"prev");});
    cards[0].classList.add("on");dots[0].classList.add("on");idx=0;curLayer=0;curCap=-1;
    cntEl.textContent="1 / "+len;updateHud();loadAudio(0);
    last=performance.now();requestAnimationFrame(loop);
  }
  if(document.readyState!=="loading")init();
  else document.addEventListener("DOMContentLoaded",init);
})();
;
