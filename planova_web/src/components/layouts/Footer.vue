<script setup>
import { ref } from 'vue';

const currentYear = ref(new Date().getFullYear());
</script>

<template>
  <footer>
    <div class="footer-main">
      <div class="container footer-container">
        <!-- 브랜드 -->
        <div class="footer-brand">
          <h2 class="brand-title">플래노바 PLANOVA</h2>
          <p class="brand-description">
            학습부터 취업 준비까지,<br>모두 한 곳에서, 모두 무료로.
          </p>
          <div class="social-links">
            <a href="#" class="social-icon"><i class="fa-brands fa-instagram"></i></a>
            <a href="#" class="social-icon"><i class="fa-brands fa-facebook"></i></a>
            <a href="#" class="social-icon"><i class="fa-brands fa-youtube"></i></a>
          </div>
        </div>

        <!-- 서비스 링크 -->
        <div class="links-column">
          <h3>서비스</h3>
          <ul>
            <li><router-link to="/student/pdf">AI 학습 플랜</router-link></li>
            <li><router-link to="/student/resume">이력서·포트폴리오</router-link></li>
            <li><router-link to="/student/coverletter">자기소개서</router-link></li>
            <li><router-link to="/student/jobs">기업 공고 조사</router-link></li>
            <li class="separator"></li>
            <li><router-link to="/support/service">고객지원 바로가기</router-link></li>
            <li><a href="#">개인정보처리방침</a></li>
            <li><a href="#">이용약관</a></li>
          </ul>
        </div>

        <!-- 고객센터 -->
        <div class="links-column contact-info">
          <h3>고객센터</h3>
          <p class="phone">010-9843-6764</p>
          <p class="email-contact">support@planova.co.kr</p>
          <p class="hours">평일 10:00 - 18:00</p>
          <p class="hours">(점심시간 13:00 - 14:00)</p>
          <p class="hours">주말 및 공휴일 휴무</p>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="container">
        <div class="copyright">
          <p><i class="fa-regular fa-copyright"></i> {{ currentYear }} 플래노바 PLANOVA. All rights reserved.</p>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
footer {
  width: 100%;
  color: #212529;
  font-family: 'Noto Sans KR', sans-serif;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.footer-main {
  padding: 60px 0;
  width: 100%;
}

.footer-container {
  display: flex;
  flex-wrap: wrap;
  gap: 40px;
}

.footer-brand {
  flex: 1.5;
  min-width: 220px;
}

.brand-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #F76707;
}

.brand-description {
  font-size: 14px;
  line-height: 1.6;
  color: #495057;
  margin-bottom: 20px;
}

.social-links {
  display: flex;
  gap: 10px;
}

.social-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: #f1f3f5;
  color: #495057;
  transition: all 0.2s;
  text-decoration: none;
}

.social-icon:hover {
  background-color: #F76707;
  color: #ffffff;
}

.links-column {
  flex: 1;
  min-width: 160px;
}

.links-column h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 18px;
  color: #343a40;
}

.links-column ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.links-column ul li {
  margin-bottom: 10px;
}

.links-column ul li.separator {
  height: 1px;
  background-color: #e9ecef;
  margin: 14px 0;
}

.links-column ul li a,
.links-column ul li router-link {
  color: #495057;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.links-column ul li a:hover {
  color: #F76707;
}

.contact-info .phone {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #F76707;
}

.contact-info .email-contact {
  font-size: 14px;
  color: #495057;
  margin-bottom: 10px;
}

.contact-info .hours {
  font-size: 13px;
  line-height: 1.6;
  color: #6c757d;
  margin-bottom: 3px;
}

.footer-bottom {
  padding: 20px 0;
  width: 100%;
  border-top: 1px solid #e9ecef;
}

.copyright {
  text-align: center;
  font-size: 12px;
  color: #6c757d;
}

@media (max-width: 768px) {
  .footer-container {
    flex-direction: column;
    gap: 32px;
  }

  .footer-brand {
    flex: none;
  }
}
</style>
