<script setup>
import { ref } from 'vue';

const currentYear = ref(new Date().getFullYear());
const email = ref('');

const subscribe = () => {
  console.log('구독 이메일:', email.value);
  email.value = '';
};
</script>

<template>
  <footer>
    <div class="footer-main">
      <div class="container footer-container">
        <div class="footer-brand">
          <h2 class="brand-title">플래노바 PLANOVA</h2>
          <p class="brand-description">
            학창시절부터 취업까지,<br>당신의 모든 계획은 플래노바가 함께합니다.
          </p>
          
          <div class="app-download">
            <p>플래노바 앱 다운로드</p>
            <div class="app-buttons">
              <button class="app-button">
                <i class="fa-brands fa-apple"></i> App Store
              </button>
              <button class="app-button">
                <i class="fa-brands fa-google-play"></i> Google Play
              </button>
            </div>
          </div>
        </div>

        <div class="footer-links">
          <div class="links-column">
            <h3>플래노바 서비스</h3>
            <ul>
              <li><a href="#">AI 학습 플랜</a></li>
              <li><a href="#">이력서·포트폴리오</a></li>
              <li><a href="#">자기소개서</a></li>
              <li><a href="#">기업 공고 조사</a></li>
            </ul>
          </div>

          <div class="links-column">
            <h3>회사 소개</h3>
            <ul>
              <li><a href="#">회사 정보</a></li>
              <li><a href="#">플래노바 스토리</a></li>
              <li><a href="#">팀 소개</a></li>
              <li><a href="#">파트너십</a></li>
            </ul>
          </div>

          <div class="links-column">
            <h3>지원 및 정책</h3>
            <ul>
              <li><a href="#">자주 묻는 질문</a></li>
              <li><a href="#">고객 지원</a></li>
              <li><a href="#">이용약관</a></li>
              <li><a href="#">개인정보처리방침</a></li>
            </ul>
          </div>

          <div class="links-column contact-info">
            <h3>고객센터</h3>
            <p class="phone">02-1234-5678</p>
            <p class="hours">평일 10:00 - 18:00</p>
            <p class="hours">(점심시간 13:00 - 14:00)</p>
            <p class="hours">주말 및 공휴일 휴무</p>
            <div class="social-links">
              <a href="#" class="social-icon"><i class="fa-brands fa-instagram"></i></a>
              <a href="#" class="social-icon"><i class="fa-brands fa-facebook"></i></a>
              <a href="#" class="social-icon"><i class="fa-brands fa-youtube"></i></a>
              <a href="#" class="social-icon"><i class="fa-solid fa-comment"></i></a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <div class="container">
        <div class="company-info">
          <p>주식회사 플래노바 | 대표: 김플래노바 | 사업자등록번호: 123-45-67890 | 통신판매업신고: 제2023-서울강남-1234호</p>
          <p>주소: 서울특별시 광진구 군자로98 | 개인정보관리책임자: 김플래노바 (privacy@planova.co.kr)</p>
          <p>고객센터: 010-9843-6764 | 이메일: support@planova.co.kr | 운영시간: 평일 10:00-18:00 (점심시간 13:00-14:00)</p>
        </div>
        <div class="copyright">
          <p><i class="fa-regular fa-copyright"></i> {{ currentYear }} 플래노바 planova Inc. All rights reserved.</p>
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

.newsletter-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #FF6B01;
}

.footer-main {
  padding: 60px 0;
  width: 100%;
}

.footer-container {
  display: flex;
  flex-wrap: wrap;
}

.footer-brand {
  width: 30%;
  padding-right: 40px;
}

.brand-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
  color: #FF6B01;
}

.brand-description {
  font-size: 14px;
  line-height: 1.6;
  color: #495057;
  margin-bottom: 20px;
}

.app-download {
  margin-top: 25px;
}

.app-download p {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #495057;
}

.app-buttons {
  display: flex;
  gap: 10px;
}

.app-button {
  background-color: #f8f9fa;
  border: 1px solid #ced4da;
  color: #212529;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.app-button:hover {
  background-color: #e9ecef;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  width: 70%;
}

.links-column {
  width: 25%;
  padding-right: 15px;
}

.links-column h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #343a40;
}

.links-column ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.links-column ul li {
  margin-bottom: 12px;
}

.links-column ul li a {
  color: #495057;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.links-column ul li a:hover {
  color: #FF6B01;
}

.contact-info .phone {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
  color: #FF6B01;
}

.contact-info .hours {
  font-size: 13px;
  line-height: 1.6;
  color: #495057;
  margin-bottom: 5px;
}

.social-links {
  display: flex;
  gap: 12px;
  margin-top: 20px;
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
}

.social-icon:hover {
  background-color: #FF6B01;
  color: #ffffff;
}

.footer-bottom {
  padding: 25px 0;
  width: 100%;
  border-top: 1px solid #e9ecef;
}

.company-info {
  margin-bottom: 12px;
  text-align: center;
}

.company-info p {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 5px;
}

.copyright {
  text-align: center;
  font-size: 12px;
  color: #6c757d;
}

@media (max-width: 992px) {
  .footer-brand, .footer-links {
    width: 100%;
  }
  
  .footer-brand {
    margin-bottom: 40px;
    padding-right: 0;
  }
  
  .links-column {
    width: 50%;
    margin-bottom: 30px;
  }
}

@media (max-width: 768px) {
  .newsletter-form {
    flex-direction: column;
  }
  
  .newsletter-form input {
    border-radius: 4px;
    margin-bottom: 10px;
  }
  
  .subscribe-btn {
    border-radius: 4px;
    padding: 12px 15px;
  }
  
  .awards-list {
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }
}

@media (max-width: 576px) {
  .links-column {
    width: 100%;
  }
  
  .app-buttons {
    flex-direction: column;
  }
}
</style>