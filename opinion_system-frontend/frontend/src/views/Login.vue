<template>

<div 
class="login-page"
:style="{backgroundImage:`url(${bg})`}"
>


<!-- 背景遮罩 -->

<div class="bg-mask"></div>

<div class="signal-layer" aria-hidden="true">
  <span
    v-for="point in signalPoints"
    :key="point.label"
    class="signal-point"
    :class="`level-${point.level}`"
    :style="{
      left: `${point.x}%`,
      top: `${point.y}%`,
      animationDelay: `${point.delay}s`,
    }"
  >
    <i></i>
    <b>{{ point.label }}</b>
  </span>
</div>



<!-- =====================
顶部导航
===================== -->

<header class="header">


<div class="brand-area">

<div class="brand-mark">

舆见

</div>

</div>





<nav class="nav">



<!-- 发现 -->

<div class="nav-item">


<button 
class="nav-btn ripple-btn"
type="button"
@mouseenter="activeMenu='发现'"
@click.prevent="handleNavClick('发现')"
>

<span>
发现
</span>

</button>



<div class="menu-panel">


<div class="menu-item" @click.stop="handleNavClick('今日热点')">

<h4>
🔥 今日热点
</h4>

<p>
实时发现网络热点事件
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('热榜排行')">

<h4>
📈 热榜排行
</h4>

<p>
查看全网热度变化
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('数据来源')">

<h4>
🌐 数据来源
</h4>

<p>
新闻与社交平台数据</p>

</div>



</div>



</div>







<!-- 分析 -->

<div class="nav-item">


<button 
class="nav-btn ripple-btn"
type="button"
@mouseenter="activeMenu='分析'"
@click.prevent="handleNavClick('分析')"
>

<span>
分析
</span>

</button>



<div class="menu-panel">



<div class="menu-item" @click.stop="handleNavClick('情感分析')">

<h4>
📊 情感分析
</h4>

<p>
分析公众态度变化
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('趋势预测')">

<h4>
📈 趋势预测
</h4>

<p>
预测舆情发展方向
</p>

</div>




<div class="menu-item" @click.stop="handleNavClick('事件聚合')">

<h4>
🔍 事件聚合
</h4>

<p>
发现相似热点事件
</p>

</div>


</div>


</div>







<!-- AI助手 -->

<div class="nav-item">


<button 
class="nav-btn ripple-btn"
type="button"
@mouseenter="activeMenu='AI助手'"
@click.prevent="handleNavClick('AI助手')"
>

<span>
AI助手
</span>

</button>



<div class="menu-panel">


<div class="menu-item" @click.stop="handleNavClick('AI问答')">

<h4>
🤖 AI问答
</h4>

<p>
智能解读热点事件
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('自动总结')">

<h4>
📝 自动总结
</h4>

<p>
生成舆情分析报告
</p>

</div>




<div class="menu-item" @click.stop="handleNavClick('智能建议')">

<h4>
💡 智能建议
</h4>

<p>
辅助判断事件趋势
</p>

</div>


</div>


</div>







<!-- 社区 -->

<div class="nav-item">


<button 
class="nav-btn ripple-btn"
type="button"
@mouseenter="activeMenu='社区'"
@click.prevent="handleNavClick('社区')"
>

<span>
社区
</span>

</button>




<div class="menu-panel">


<div class="menu-item" @click.stop="handleNavClick('热门讨论')">

<h4>
🔥 热门讨论
</h4>

<p>
查看用户观点
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('观点交流')">

<h4>
💬 观点交流
</h4>

<p>
分析公众情绪变化
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('话题广场')">

<h4>
📌 话题广场
</h4>

<p>
探索热门话题
</p>

</div>


</div>


</div>








<!-- 关于我们 -->


<div class="nav-item">


<button 
class="nav-btn ripple-btn"
type="button"
@mouseenter="activeMenu='关于我们'"
@click.prevent="handleNavClick('关于我们')"
>

<span>
关于我们
</span>

</button>



<div class="menu-panel">


<div class="menu-item" @click.stop="handleNavClick('平台介绍')">

<h4>
🏢 平台介绍
</h4>

<p>
了解舆见系统
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('技术架构')">

<h4>
⚙️ 技术架构</h4>

<p>
数据采集与AI分析
</p>

</div>



<div class="menu-item" @click.stop="handleNavClick('核心能力')">

<h4>
🚀 核心能力
</h4>

<p>
智能舆情洞察平台
</p>

</div>



</div>



</div>




</nav>






<!-- 登录注册 -->

<div class="account">


<button
class="top-btn ripple-btn"
type="button"
@click="openLogin"
>

<span>
登录
</span>

</button>




<button
class="top-btn ripple-btn"
type="button"
@click="openRegister"
>

<span>
注册
</span>

</button>



</div>



</header>









<!-- =====================
左侧内容
===================== -->


<section class="left-area">


<div class="brand-box">



<div class="brand-line">

<h1>
舆见
</h1>


<span>
OPINION INSIGHT
</span>


</div>




<div class="sub-title">

智能舆情洞察与分析平台
</div>





<h2>

发现每天正在发生的事情
</h2>






<div class="feature-list">


<p>
实时追踪热点事件
</p>


<p>
分析公众观点变化
</p>


<p>
洞察网络舆论趋势
</p>


</div>







<div class="actions">


<button
class="main-btn ripple-btn"
type="button"
@click="openLogin"
>

<span>
立即体验
</span>

</button>




<button
class="second-btn ripple-btn"
type="button"
@click="guestMode"
>

<span>
游客浏览
</span>

</button>



</div>





</div>


</section>









<!-- =====================
右侧视觉区域
===================== -->


<section class="right-area">



<div class="visual-box">





<div class="visual-title">

智能舆情分析

</div>







<!-- 数据卡片 -->


<div class="data-card hot-card">


<h3>
热点指数
</h3>


<strong>
98.6
</strong>


<p>
实时热度变化

</p>


</div>






<div class="data-card emotion-card">


<h3>
情感趋势
</h3>


<div class="mini-chart">

<span></span>
<span></span>
<span></span>
<span></span>

</div>


</div>








<!-- 手机 -->

<div class="phone">


<div class="phone-notch">

</div>




<div class="phone-header">


<b>
舆见
</b>


<span>
今日热点
</span>


</div>





<div class="phone-card">


<h4>
热门事件
</h4>


<p>
社会热点持续升温

</p>


<div class="tag">

#热点

</div>



</div>






<div class="phone-card">


<h4>
情感分析

</h4>


<div class="progress">

<div></div>

</div>


<p>
正面 62%  中立25% 负面13%

</p>



</div>






<div class="phone-card">


<h4>
用户讨论

</h4>


<p>

#社会

#科技

#娱乐

</p>


</div>





</div>










<!-- 浮动标签 -->


<div class="float-tag tag-one">

#社会

</div>



<div class="float-tag tag-two">

#科技

</div>




<div class="float-tag tag-three">

AI分析

</div>





<div class="float-tag tag-four">

舆情预测

</div>





</div>



</section>









<!-- =====================
登录注册弹窗
===================== -->


<AuthModal />






</div>

</template>
<script setup>

import {
  ref,
  onMounted
} from "vue"

import { useRouter } from "vue-router"
import { useUserStore } from "@/stores/user"
import { useLoginPromptStore } from "@/stores/loginPrompt"
import AuthModal from "@/components/AuthModal.vue"



import bg from "@/assets/login-bg.png"




// =====================
// 登录注册状态
// =====================


const router = useRouter()


const userStore = useUserStore()
const loginPrompt = useLoginPromptStore()

const signalPoints = [
  { label: "北京", x: 71.05, y: 31.88, level: 3, delay: 0 },
  { label: "上海", x: 77.39, y: 56.54, level: 2, delay: 0.35 },
  { label: "广州", x: 68.78, y: 79.49, level: 2, delay: 0.7 },
  { label: "成都", x: 55.38, y: 58.45, level: 1, delay: 1.05 },
  { label: "西安", x: 59.81, y: 46.76, level: 1, delay: 1.4 },
  { label: "武汉", x: 66.51, y: 60.15, level: 2, delay: 1.75 },
  { label: "杭州", x: 75.72, y: 60.36, level: 1, delay: 2.1 },
  { label: "重庆", x: 58.85, y: 64.19, level: 1, delay: 2.45 },
]




// =====================
// 当前导航状态
// =====================


const activeMenu = ref("")




// =====================
// 打开登录
// =====================


function openLogin(){

  loginPrompt.openLogin()

}



// =====================
// 打开注册
// =====================


function openRegister(){

  loginPrompt.openRegister()

}



// =====================
// 游客模式
// =====================


function guestMode(){

  userStore.enterGuest()

  router.push("/home")

}


// =====================
// 顶部导航拦截
// =====================


function handleNavClick(menu){

  activeMenu.value=menu
  loginPrompt.openLogin()

}






// =====================
// 液态波纹动画
// 鼠标位置扩散
// =====================


onMounted(()=>{


  const buttons =
  document.querySelectorAll(
    ".ripple-btn"
  )



  buttons.forEach(button=>{


    button.addEventListener(
      "mousemove",
      (e)=>{


        const rect =
        button.getBoundingClientRect()



        const x =
        e.clientX - rect.left



        const y =
        e.clientY - rect.top




        button.style.setProperty(
          "--x",
          `${x}px`
        )



        button.style.setProperty(
          "--y",
          `${y}px`
        )



      }

    )



  })



})



</script>
<style scoped>





*{
  box-sizing:border-box;
}


.login-page{

  width:100vw;

  height:100vh;

  overflow:hidden;

  position:relative;

  display:flex;

  background-size:cover;

  background-position:center;

  font-family:
  "Microsoft YaHei",
  sans-serif;

}



.bg-mask{

position:absolute;

inset:0;

background:
linear-gradient(
    90deg,
   rgba(8,20,38,.62),
   rgba(8,20,38,.30)
  );
    z-index:1;
}

.signal-layer{
  position:absolute;
  inset:0;
  z-index:1;
  pointer-events:none;
}

.signal-point{
  position:absolute;
  display:flex;
  align-items:center;
  gap:7px;
  color:#dbeafe;
  font-size:11px;
  font-weight:700;
  text-shadow:0 0 14px rgba(56,189,248,.6);
  transform:translate(-50%,-50%);
  animation:signal-float 5.6s ease-in-out infinite;
}

.signal-point i{
  position:relative;
  width:8px;
  height:8px;
  border-radius:50%;
  background:#67e8f9;
  box-shadow:0 0 12px rgba(103,232,249,.9);
}

.signal-point i::before,
.signal-point i::after{
  content:"";
  position:absolute;
  inset:-9px;
  border:1px solid rgba(103,232,249,.34);
  border-radius:50%;
  animation:signal-pulse 2.7s ease-out infinite;
}

.signal-point i::after{
  inset:-16px;
  animation-delay:.45s;
}

.signal-point b{
  padding:3px 7px;
  border:1px solid rgba(125,211,252,.18);
  border-radius:999px;
  background:rgba(8,20,38,.34);
  backdrop-filter:blur(8px);
}

.signal-point.level-2 i{
  width:10px;
  height:10px;
  background:#a5b4fc;
  box-shadow:0 0 16px rgba(165,180,252,.9);
}

.signal-point.level-3 i{
  width:12px;
  height:12px;
  background:#c4b5fd;
  box-shadow:0 0 20px rgba(196,181,253,.95);
}

@keyframes signal-pulse{
  from{
    opacity:.8;
    transform:scale(.45);
  }

  to{
    opacity:0;
    transform:scale(1.9);
  }
}

@keyframes signal-float{
  50%{
    transform:translate(-50%,calc(-50% - 8px));
  }
}






/* =========================
顶部导航
========================= */


.header{

  position:absolute;

  top:0;

  left:0;

  width:100%;

  height:90px;

  padding:0 70px;

  display:flex;

  align-items:center;

  z-index:20;

}





.brand-area{

  width:55px;

}





.brand-mark{

  width:45px;

  height:45px;

  display:grid;

  place-items:center;

  border-radius:16px;


  background:linear-gradient(135deg, rgba(15,30,58,.94), rgba(37,99,235,.82));

  color:#f8fbff;

  font-size:15px;

  font-weight:900;

  letter-spacing:.08em;

  text-shadow:0 0 14px rgba(56,189,248,.46);


  position:relative;

  transition:.35s;

}





.brand-mark:hover{

  transform:
  rotate(15deg)
  scale(1.08);

}





.brand-mark::after{

  content:"";

  position:absolute;

  inset:0;

  border:1px solid rgba(255,255,255,.14);

  background:linear-gradient(135deg, rgba(255,255,255,.16), transparent 55%);

  border-radius:inherit;

  pointer-events:none;

}






.nav{

  display:flex;

  gap:18px;

  margin-left:60px;

}



.nav-item{

  position:relative;

}






/* =========================
按钮液态动画
========================= */


.nav-btn,
.top-btn,
.main-btn,
.second-btn,
.submit-btn{


  position:relative;
    z-index:1;
  overflow:hidden;

  isolation:isolate;
  border:none;


  border-radius:35px;


  cursor:pointer;


  padding:13px 28px;


  font-size:15px;


  background:

  rgba(255,255,255,.88);


  backdrop-filter:

  blur(20px);


  box-shadow:

  0 10px 30px rgba(0,0,0,.08);


  transition:.35s;


}


/* =========================
按钮文字层级
防止液态动画遮挡文字
========================= */


/* =========================
所有按钮文字层级
防止液态动画遮挡
========================= */

.nav-btn span,
.top-btn span,
.main-btn span,
.second-btn span,
.submit-btn span{

  position:relative;

  z-index:3;

}



.nav-btn::before,
.top-btn::before,
.main-btn::before,
.second-btn::before,
.submit-btn::before{


  content:"";


  position:absolute;


  width:10px;


  height:10px;


  left:var(--x,50%);


  top:var(--y,50%);



  border-radius:50%;



  background:


  radial-gradient(
  circle,
  #c4b5fd,
  #7c3aed
  );



  transform:

  translate(-50%,-50%)
  scale(0);



  transition:

  transform .6s cubic-bezier(.16,1,.3,1);


  z-index:0;


}





.nav-btn:hover::before,
.top-btn:hover::before,
.main-btn:hover::before,
.second-btn:hover::before,
.submit-btn:hover::before{


  transform:

  translate(-50%,-50%)
  scale(25);


}



.nav-btn:hover,
.top-btn:hover,
.main-btn:hover,
.submit-btn:hover{

  color:white;

}



.nav-btn:hover,
.top-btn:hover,
.main-btn:hover,
.second-btn:hover{


  transform:

  translateY(-3px);


}
.main-btn:active,
.top-btn:active,
.submit-btn:active{

  transform:scale(.96);

}







/* =========================
登录按钮
========================= */


.account{

  margin-left:auto;

}



.top-btn{

  margin-left:15px;

}





/* =========================
下拉菜单
========================= */


.menu-panel{

  position:absolute;

  top:55px;

  left:50%;

  transform:
  translateX(-50%)
  translateY(15px)
  scale(.95);


  width:240px;

  padding:14px;


  background:
  rgba(255,255,255,.82);


  backdrop-filter:
  blur(25px);


  border-radius:24px;


  box-shadow:
  0 25px 60px rgba(0,0,0,.12);


  opacity:0;

  visibility:hidden;

  pointer-events:none;


  transition:
  all .35s cubic-bezier(.16,1,.3,1);


  z-index:999;

}



/* 创建隐藏连接区域 */

.menu-panel::before{

  content:"";

  position:absolute;

  left:0;

  top:-20px;

  width:100%;

  height:20px;

}





.nav-item:hover .menu-panel,
.menu-panel:hover{


  opacity:1;


  visibility:visible;


  pointer-events:auto;


  transform:

  translateX(-50%)
  translateY(0)
  scale(1);


}



.nav-item:hover .menu-panel,
.menu-panel:hover{


  opacity:1;


  visibility:visible;


  pointer-events:auto;



  transform:


  translateX(-50%)
  translateY(0)
  scale(1);



}






.menu-item{


  padding:14px;


  border-radius:16px;


  transition:.3s;


}



.menu-item:hover{


  background:#805cff;


  transform:
  translateX(6px);


}



.menu-item h4{


  margin:0;


  font-size:15px;


}



.menu-item p{


  margin-top:6px;


  font-size:12px;


  color:#94a3b8;


}









/* =========================
左侧区域
========================= */


.left-area{


  width:45%;


  height:100vh;


  position:relative;


  z-index:2;


}




.brand-box{


  position:absolute;


  left:120px;


  top:220px;


}





.brand-line{


  display:flex;


  align-items:center;


  gap:20px;


}

.brand-line h1{


  margin:0;


  font-size:58px;


  font-weight:800;


}



.brand-line span{


  font-size:22px;


  letter-spacing:4px;


  color:#94a3b8;


}





.sub-title{


  margin-top:20px;


  color:#94a3b8;


  font-size:17px;


}





.brand-box h2{


  margin-top:35px;


  font-size:38px;


  line-height:1.4;


}






.feature-list{


  margin-top:35px;


  color:#e2e8f0;


  font-size:17px;


}



.feature-list p{


  margin:12px 0;


}






.actions{


  display:flex;


  gap:20px;


  margin-top:35px;


}





.main-btn{


  background:#805cff;


  color:white;


}



.second-btn{


  background:rgba(15,30,58,.72);


}








/* =========================
右侧区域
========================= */


.right-area{


  width:55%;


  height:100vh;


  display:flex;


  align-items:center;


  justify-content:center;


  z-index:2;


}





.visual-box{


  width:700px;


  height:650px;


  position:relative;


  border-radius:50px;



  background:


  rgba(255,255,255,.55);



  backdrop-filter:

  blur(25px);



  box-shadow:


  0 30px 80px rgba(0,0,0,.1);



}






.visual-title{


  position:absolute;


  top:35px;


  width:100%;


  text-align:center;


  font-size:22px;


  font-weight:bold;


}








/* 手机 */


.phone{


  position:absolute;


  left:220px;


  top:80px;


  width:290px;


  height:580px;



  background:linear-gradient(180deg, rgba(15,30,58,.98), rgba(8,20,38,.98));


  border:8px solid #222;


  border-radius:45px;



  padding:20px;



  box-shadow:


  0 40px 90px rgba(0,0,0,.2);



}






.phone-notch{


  width:100px;


  height:22px;


  background:#222;


  border-radius:

  0 0 15px 15px;



  margin:auto;


}




.phone-header{


  display:flex;


  justify-content:space-between;


  margin-top:20px;


}



.phone-header span{


  color:#94a3b8;


  font-size:12px;


}






.phone-card{


  margin-top:20px;


  padding:15px;


  border-radius:20px;


  background:#f7f7fb;


}



.phone-card p{


  font-size:13px;


  color:#94a3b8;


}



.tag{


  display:inline-block;


  background:#eee8ff;


  color:#805cff;


  padding:5px 12px;


  border-radius:20px;


}





.progress{


  height:8px;


  background:#ddd;


  border-radius:10px;


}



.progress div{


  width:62%;


  height:100%;


  background:#805cff;


  border-radius:10px;


}









/* 数据卡片 */


.data-card{


  position:absolute;


  background:rgba(15,30,58,.75);


  padding:22px;


  border-radius:25px;


  box-shadow:


  0 20px 40px rgba(0,0,0,.12);


}




.hot-card{


  left:40px;


  top:160px;


}



.emotion-card{


  right:40px;


  top:250px;


}



.data-card strong{


  font-size:42px;


  color:#805cff;


}






.mini-chart{


  display:flex;


  gap:8px;


  height:60px;


  align-items:end;


}



.mini-chart span{


  width:12px;


  background:#805cff;


  border-radius:8px;


}



.mini-chart span:nth-child(1){

height:20px;

}

.mini-chart span:nth-child(2){

height:35px;

}

.mini-chart span:nth-child(3){

height:45px;

}

.mini-chart span:nth-child(4){

height:55px;

}









/* 浮动标签 */


.float-tag{


  position:absolute;


  padding:12px 22px;


  border-radius:30px;


  background:rgba(37,99,235,.18);


  box-shadow:


  0 15px 35px rgba(0,0,0,.12);



  animation:

  float 4s infinite ease-in-out;


}



.tag-one{

left:90px;

top:80px;

}



.tag-two{

right:90px;

top:100px;

}



.tag-three{

left:100px;

bottom:90px;

}



.tag-four{

right:100px;

bottom:100px;

}






@keyframes float{


50%{

transform:

translateY(-15px);

}


}









/* =========================
弹窗
========================= */


.modal-mask{


position:fixed;


inset:0;


background:

rgba(0,0,0,.25);


display:flex;


align-items:center;


justify-content:center;


z-index:100;



}





.modal-box{


width:400px;


padding:45px;


border-radius:30px;


background:

rgba(255,255,255,.9);



backdrop-filter:

blur(25px);



box-shadow:


0 30px 80px rgba(0,0,0,.25);



animation:

pop .45s cubic-bezier(.16,1,.3,1);


}




@keyframes pop{


from{


opacity:0;


transform:

scale(.7);


}



to{


opacity:1;


transform:

scale(1);


}


}





.modal-box input{


width:100%;


height:48px;


margin-top:18px;


border-radius:12px;


border:1px solid #ddd;


padding-left:15px;


}





.submit-btn{


width:100%;


margin-top:25px;


height:48px;


background:#805cff;


color:white;


}




.close-btn{


position:absolute;


right:20px;


top:15px;


border:none;


background:none;


font-size:28px;


cursor:pointer;


}



.switch{


margin-top:25px;


text-align:center;


color:#805cff;


cursor:pointer;


}



/* =====================
深蓝科技新闻 + AI 数据分析主题覆盖
仅换肤，不改变结构和交互
===================== */

.login-page{
  color:#e2e8f0;
  background-color:#081426;
}

.bg-mask{
  background:
  radial-gradient(circle at 18% 18%, rgba(37,99,235,.1), transparent 28%),
  radial-gradient(circle at 78% 24%, rgba(139,92,246,.08), transparent 30%),
  radial-gradient(circle at 55% 84%, rgba(0,217,255,.05), transparent 32%),
  rgba(8,20,38,.08);
}

.bg-mask::after{
  content:"";
  position:absolute;
  inset:0;
  background-image:
  linear-gradient(rgba(56,189,248,.032) 1px, transparent 1px),
  linear-gradient(90deg, rgba(56,189,248,.032) 1px, transparent 1px);
  background-size:44px 44px;
  mask-image:linear-gradient(to bottom, rgba(0,0,0,.7), transparent 82%);
}

.brand-mark{
  background:linear-gradient(135deg, rgba(15,30,58,.94), rgba(37,99,235,.82));
  color:#f8fbff;
  box-shadow:0 18px 40px rgba(37,99,235,.34), inset 0 1px 0 rgba(255,255,255,.16);
}

.nav-btn,
.top-btn{
  border:1px solid rgba(255,255,255,.12);
  background:rgba(15,30,58,.72);
  color:#cbd5e1;
  box-shadow:0 16px 40px rgba(0,0,0,.22);
  backdrop-filter:blur(20px);
}

.nav-btn:hover,
.top-btn:hover{
  color:#fff;
  border-color:rgba(56,189,248,.32);
}

.nav-item:hover .nav-btn{
  background:rgba(37,99,235,.2);
}

.menu-panel{
  border:1px solid rgba(255,255,255,.12);
  background:
  linear-gradient(145deg, rgba(15,30,58,.88), rgba(8,20,38,.72)),
  rgba(15,30,58,.85);
  box-shadow:0 24px 70px rgba(0,0,0,.28);
  backdrop-filter:blur(22px);
}

.menu-item{
  color:#e2e8f0;
}

.menu-item:hover{
  background:linear-gradient(135deg, rgba(37,99,235,.92), rgba(139,92,246,.92));
  box-shadow:0 14px 30px rgba(37,99,235,.22);
}

.menu-item h4{
  color:#e2e8f0;
}

.menu-item p{
  color:#94a3b8;
}

.brand-line h1,
.brand-box h2,
.visual-title,
.phone-header b,
.phone-card h4,
.modal-box h2{
  color:#fff;
}

.brand-line span,
.sub-title,
.feature-list,
.phone-header span,
.phone-card p,
.data-card h3,
.data-card p,
.modal-box p{
  color:#94a3b8;
}

.brand-line h1{
  text-shadow:0 0 34px rgba(56,189,248,.16);
}

.main-btn,
.submit-btn{
  background:linear-gradient(135deg, #2563eb, #8b5cf6);
  color:#fff;
  box-shadow:0 20px 48px rgba(37,99,235,.3);
}

.second-btn{
  border:1px solid rgba(255,255,255,.12);
  background:rgba(15,30,58,.72);
  color:#e2e8f0;
  box-shadow:0 18px 44px rgba(0,0,0,.22);
}

.visual-box,
.data-card,
.float-tag,
.modal-box{
  border:1px solid rgba(255,255,255,.12);
  background:
  linear-gradient(145deg, rgba(15,30,58,.84), rgba(8,20,38,.72)),
  rgba(15,30,58,.75);
  box-shadow:0 28px 80px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.08);
  backdrop-filter:blur(22px);
}

.phone{
  border-color:#1e293b;
  background:
  linear-gradient(180deg, rgba(15,30,58,.98), rgba(8,20,38,.98));
  box-shadow:0 40px 90px rgba(0,0,0,.34);
}

.phone-notch{
  background:#020617;
}

.phone-card{
  border:1px solid rgba(255,255,255,.1);
  background:rgba(255,255,255,.08);
}

.tag,
.float-tag{
  color:#93c5fd;
  background:rgba(37,99,235,.18);
}

.data-card strong{
  color:#38bdf8;
}

.progress{
  background:rgba(148,163,184,.24);
}

.progress div,
.line-chart{
  background:#38bdf8;
  border-color:#38bdf8;
}

.modal-mask{
  background:
  radial-gradient(circle at 50% 42%, rgba(37,99,235,.24), transparent 32%),
  rgba(2,6,23,.62);
  backdrop-filter:blur(14px);
}

.modal-box input{
  border:1px solid rgba(255,255,255,.12);
  background:rgba(255,255,255,.08);
  color:#fff;
}

.modal-box input::placeholder{
  color:#94a3b8;
}

.close-btn,
.switch{
  color:#38bdf8;
}

.ripple-btn::before{
  background:radial-gradient(circle, #00d9ff, #2563eb 48%, #8b5cf6);
}



/* =====================
右侧产品展示精修
只优化视觉质感，不改变布局/结构/位置
===================== */

.visual-box{
  border:1px solid rgba(255,255,255,.15);
  background:
  radial-gradient(circle at 50% 34%, rgba(37,99,235,.18), transparent 32%),
  radial-gradient(circle at 72% 66%, rgba(139,92,246,.14), transparent 30%),
  rgba(255,255,255,.08);
  box-shadow:
  0 0 80px rgba(37,99,235,.35),
  0 0 120px rgba(139,92,246,.25),
  inset 0 1px 0 rgba(255,255,255,.12);
  backdrop-filter:blur(25px);
}

.visual-box::before{
  content:"";
  position:absolute;
  inset:22px;
  border-radius:42px;
  pointer-events:none;
  background:
  linear-gradient(90deg, rgba(0,217,255,.08) 1px, transparent 1px),
  linear-gradient(rgba(0,217,255,.08) 1px, transparent 1px);
  background-size:34px 34px;
  mask-image:radial-gradient(circle at 50% 48%, rgba(0,0,0,.72), transparent 68%);
  opacity:.55;
}

.visual-box::after{
  content:"";
  position:absolute;
  left:50%;
  top:50%;
  width:390px;
  height:390px;
  border-radius:50%;
  pointer-events:none;
  background:
  radial-gradient(circle, rgba(0,217,255,.16), rgba(37,99,235,.08) 42%, transparent 70%);
  transform:translate(-50%,-50%);
  filter:blur(4px);
}

.visual-title{
  color:#e0e7ff;
  text-shadow:
  0 0 20px rgba(37,99,235,.5),
  0 0 34px rgba(0,217,255,.22);
  letter-spacing:.04em;
}

.phone{
  border:1px solid rgba(255,255,255,.16);
  background:
  linear-gradient(145deg, rgba(23,37,84,.98), rgba(15,23,42,.98));
  box-shadow:
  0 42px 90px rgba(0,0,0,.34),
  0 0 70px rgba(37,99,235,.28),
  0 0 110px rgba(139,92,246,.16),
  inset 0 1px 0 rgba(255,255,255,.16);
}

.phone::before{
  content:"";
  position:absolute;
  inset:12px;
  z-index:0;
  border-radius:34px;
  background:
  radial-gradient(circle at 30% 18%, rgba(0,217,255,.14), transparent 28%),
  radial-gradient(circle at 82% 12%, rgba(139,92,246,.16), transparent 30%),
  linear-gradient(180deg, rgba(255,255,255,.055), rgba(255,255,255,.02));
  pointer-events:none;
}

.phone > *{
  position:relative;
  z-index:1;
}

.phone-notch{
  background:linear-gradient(135deg, #020617, #172554);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12);
}

.phone-header b{
  color:#f8fafc;
}

.phone-header span{
  color:#93c5fd;
}

.phone-card{
  border:1px solid rgba(255,255,255,.12);
  background:
  linear-gradient(145deg, rgba(255,255,255,.1), rgba(255,255,255,.045));
  box-shadow:
  0 12px 28px rgba(0,0,0,.18),
  inset 0 1px 0 rgba(255,255,255,.08);
  backdrop-filter:blur(12px);
}

.phone-card h4{
  color:#e0e7ff;
}

.phone-card p{
  color:#94a3b8;
}

.data-card{
  border:1px solid rgba(255,255,255,.15);
  background:
  linear-gradient(145deg, rgba(255,255,255,.14), rgba(255,255,255,.07));
  box-shadow:
  0 18px 42px rgba(0,0,0,.22),
  0 0 36px rgba(37,99,235,.12),
  inset 0 1px 0 rgba(255,255,255,.12);
  backdrop-filter:blur(15px);
}

.data-card h3{
  color:#e2e8f0;
}

.data-card p{
  color:#94a3b8;
}

.data-card strong{
  color:#38bdf8;
  text-shadow:0 0 24px rgba(0,217,255,.32);
}

.emotion-card .line-chart{
  background:transparent;
  border-bottom-color:#00d9ff;
  box-shadow:0 10px 26px rgba(0,217,255,.18);
}

.float-tag{
  border:1px solid rgba(255,255,255,.15);
  background:
  linear-gradient(145deg, rgba(255,255,255,.15), rgba(255,255,255,.07));
  color:#e0e7ff;
  box-shadow:
  0 16px 38px rgba(0,0,0,.22),
  0 0 34px rgba(37,99,235,.14),
  inset 0 1px 0 rgba(255,255,255,.12);
  backdrop-filter:blur(15px);
}

.tag-three{
  color:#ddd6fe;
  box-shadow:
  0 16px 38px rgba(0,0,0,.22),
  0 0 34px rgba(139,92,246,.2),
  inset 0 1px 0 rgba(255,255,255,.12);
}

.tag-four{
  color:#a5f3fc;
  box-shadow:
  0 16px 38px rgba(0,0,0,.22),
  0 0 34px rgba(0,217,255,.18),
  inset 0 1px 0 rgba(255,255,255,.12);
}

.tag{
  border:1px solid rgba(56,189,248,.18);
  background:rgba(37,99,235,.18);
  color:#bfdbfe;
}

.progress{
  background:rgba(148,163,184,.18);
}

.progress div{
  background:linear-gradient(90deg, #2563eb, #00d9ff);
  box-shadow:0 0 18px rgba(0,217,255,.32);
}



</style>
