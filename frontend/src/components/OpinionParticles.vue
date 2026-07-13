<template>
  <div class="particle-layer">


    <div class="info-card card-one">

      <div class="card-title">
        热点监测
      </div>

      <div class="card-value">
        实时舆情追踪
      </div>

      <div class="card-line"></div>

      <div class="card-desc">
        数据动态更新
      </div>

    </div>



    <div class="info-card card-two">

      <div class="card-title">
        情感分析
      </div>

      <div class="emotion">

        <span>
          正面 62%
        </span>

        <span>
          中性 25%
        </span>

        <span>
          负面 13%
        </span>

      </div>

    </div>




    <div class="keyword keyword-one">
      热点
    </div>


    <div class="keyword keyword-two">
      舆情
    </div>


    <div class="keyword keyword-three">
      AI
    </div>


    <div class="keyword keyword-four">
      传播分析
    </div>



  </div>
</template>



<style scoped>


.particle-layer{

position:absolute;

inset:0;

z-index:1;

pointer-events:none;

}




.info-card{


position:absolute;


padding:18px 22px;


width:220px;


border-radius:18px;



background:

rgba(255,255,255,.08);



border:

1px solid rgba(255,255,255,.18);



backdrop-filter:blur(15px);



color:white;



animation:float 8s infinite ease-in-out;



}




.card-one{

left:50px;

top:80px;

}



.card-two{

right:50px;

bottom:80px;

animation-delay:3s;

}



.card-title{


font-size:13px;


color:#75baff;


}



.card-value{


margin-top:12px;


font-size:18px;


}



.card-line{


height:3px;


margin-top:15px;


background:#4da3ff;


border-radius:5px;


}



.card-desc{


margin-top:10px;


font-size:12px;


color:#c7ddff;


}




.emotion{


margin-top:15px;


display:flex;


flex-direction:column;


gap:8px;


font-size:13px;


}




.keyword{


position:absolute;


color:rgba(120,190,255,.45);


font-size:22px;


font-weight:bold;



animation:float 10s infinite ease-in-out;



}




.keyword-one{

left:20%;

top:25%;

}



.keyword-two{

left:35%;

bottom:20%;

}



.keyword-three{

right:35%;

top:18%;

}



.keyword-four{

right:20%;

bottom:30%;

}



@keyframes float{


0%{

transform:translateY(0);

}



50%{

transform:translateY(-20px);

}



100%{

transform:translateY(0);

}


}



</style>