<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import authApi from '@/api/authApi';

const router = useRouter();
const isLoading = ref(false);
const activeTab = ref('email'); // 'email' 또는 'kakao'

// 이메일 로그인 관련 변수
const email = ref('');
const password = ref('');
const rememberMe = ref(false);
const emailLoginError = ref('');

// 환경변수에서 카카오 키 읽기 (Vite 방식과 Vue 방식 모두 시도)
const KAKAO_KEY = import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY || 
                  import.meta.env.VUE_APP_KAKAO_JAVASCRIPT_KEY || 
                  'f4c7f7a5fe0b155d15b0fc65f67f94ec'; // 백업용 키

console.log('환경변수 확인:');
console.log('VITE_KAKAO_JAVASCRIPT_KEY:', import.meta.env.VITE_KAKAO_JAVASCRIPT_KEY);
console.log('VUE_APP_KAKAO_JAVASCRIPT_KEY:', import.meta.env.VUE_APP_KAKAO_JAVASCRIPT_KEY);
console.log('최종 사용 키:', KAKAO_KEY);

// 디버그용 변수
const debug = ref({
  kakaoKey: KAKAO_KEY,
  isKakaoLoaded: false,
  isInitialized: false
});

// 폼 유효성 검사
const isEmailValid = computed(() => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.value);
});

const isPasswordValid = computed(() => {
  return password.value.length >= 6;
});

const isFormValid = computed(() => {
  return isEmailValid.value && isPasswordValid.value;
});

// 카카오 SDK 초기화
onMounted(async () => {
  console.log('=== 디버그 정보 ===');
  console.log('카카오 키:', debug.value.kakaoKey);
  console.log('window.Kakao 존재 여부:', !!window.Kakao);
  
  // 카카오 SDK가 로드될 때까지 기다림
  let retryCount = 0;
  const maxRetries = 10;
  
  const waitForKakao = () => {
    return new Promise((resolve) => {
      const checkKakao = () => {
        if (window.Kakao && window.Kakao.isInitialized !== undefined) {
          resolve(true);
        } else if (retryCount < maxRetries) {
          retryCount++;
          console.log(`카카오 SDK 로딩 대기 중... (${retryCount}/${maxRetries})`);
          setTimeout(checkKakao, 100);
        } else {
          resolve(false);
        }
      };
      checkKakao();
    });
  };
  
  const kakaoLoaded = await waitForKakao();
  
  if (kakaoLoaded && window.Kakao) {
    debug.value.isKakaoLoaded = true;
    
    // 이제 안전하게 isInitialized 호출 가능
    if (window.Kakao.isInitialized && !window.Kakao.isInitialized()) {
      console.log('카카오 SDK 초기화 중... 키:', KAKAO_KEY);
      
      if (KAKAO_KEY === '카카오_JavaScript_키를_여기에_입력') {
        console.error('⚠️ 실제 카카오 키를 설정해주세요!');
        alert('카카오 키가 설정되지 않았습니다. 코드에서 KAKAO_KEY 변수에 실제 키를 입력해주세요.');
        return;
      }
      
      try {
        window.Kakao.init(KAKAO_KEY);
        debug.value.isInitialized = true;
        console.log('✅ 카카오 SDK 초기화 성공');
      } catch (error) {
        console.error('❌ 카카오 SDK 초기화 실패:', error);
        alert('카카오 SDK 초기화에 실패했습니다. 키를 확인해주세요.');
      }
    } else if (window.Kakao.isInitialized && window.Kakao.isInitialized()) {
      debug.value.isInitialized = true;
      console.log('✅ 카카오 SDK 이미 초기화됨');
    }
  } else {
    console.error('❌ 카카오 SDK가 로드되지 않았습니다.');
  }
});


const emailLogin = async () => {
  if (!isFormValid.value) {
    emailLoginError.value = '유효하지 않은 이메일 또는 비밀번호입니다.';
    return;
  }

  try {
    isLoading.value = true;
    emailLoginError.value = '';
    
    console.log('🧪 이메일 로그인 API 요청 시작');

    const response = await authApi.login({
      email: email.value,
      password: password.value
    });

    console.log('✅ 로그인 응답:', response);

    // 로그인 성공 시 정보 저장
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    localStorage.setItem('token_type', response.token_type);
    localStorage.setItem('user_id', response.user_id);
    localStorage.setItem('username', response.username);
    localStorage.setItem('userEmail', response.email);
    localStorage.setItem('is_admin', response.is_admin);
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('loginMethod', 'email');

    if (rememberMe.value) {
      localStorage.setItem('rememberedEmail', email.value);
    } else {
      localStorage.removeItem('rememberedEmail');
    }

    router.push({ name: 'studentMain' });

  } catch (error) {
    console.error('❌ 로그인 실패:', error);

    // FastAPI의 validation error 구조에 따라 메시지 파싱
    if (error.response?.data?.detail?.[0]?.msg) {
      emailLoginError.value = error.response.data.detail[0].msg;
    } else {
      emailLoginError.value = '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.';
    }
  } finally {
    isLoading.value = false;
  }
};


// 카카오 로그인 처리
const kakaoLogin = async () => {
  console.log('=== 로그인 시도 ===');
  console.log('카카오 로드 여부:', debug.value.isKakaoLoaded);
  console.log('카카오 초기화 여부:', debug.value.isInitialized);
  
  if (!window.Kakao) {
    alert('카카오 SDK가 로드되지 않았습니다.');
    return;
  }
  
  if (!window.Kakao.isInitialized()) {
    alert('카카오 SDK가 초기화되지 않았습니다.');
    return;
  }
  
  try {
    isLoading.value = true;
    
    // 카카오 로그인 실행
    window.Kakao.Auth.login({
      success: async (authObj) => {
        console.log('카카오 로그인 성공', authObj);
        
        // 사용자 정보 요청
        window.Kakao.API.request({
          url: '/v2/user/me',
          success: (userData) => {
            console.log('사용자 정보', userData);
            
            // 로그인 정보 저장
            localStorage.setItem('isAuthenticated', 'true');
            localStorage.setItem('kakaoToken', authObj.access_token);
            localStorage.setItem('userInfo', JSON.stringify(userData));
            localStorage.setItem('loginMethod', 'kakao');
            
            // 학생 메인 페이지로 이동
            router.push({ name: 'studentMain' });
          },
          fail: (error) => {
            console.error('사용자 정보 요청 실패', error);
            alert('사용자 정보를 가져오는데 실패했습니다.');
          }
        });
      },
      fail: (error) => {
        console.error('카카오 로그인 실패', error);
        alert('로그인에 실패했습니다. 다시 시도해주세요.');
      }
    });
  } catch (error) {
    console.error('로그인 실패:', error);
    alert('로그인 중 오류가 발생했습니다: ' + error.message);
  } finally {
    isLoading.value = false;
  }
};

// 로그아웃 (옵션)
const logout = () => {
  const loginMethod = localStorage.getItem('loginMethod');
  
  if (loginMethod === 'kakao' && window.Kakao?.Auth.getAccessToken()) {
    window.Kakao?.API.request({
      url: '/v1/user/unlink',
      success: () => {
        console.log('카카오 로그아웃 성공');
      },
      fail: (error) => {
        console.error('카카오 로그아웃 실패', error);
      }
    });
  }
  
  // 공통 로그아웃 처리
  localStorage.removeItem('isAuthenticated');
  localStorage.removeItem('kakaoToken');
  localStorage.removeItem('userInfo');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('loginMethod');
};

// 회원가입 페이지로 이동하는 함수 추가
const goToSignup = () => {
  router.push({ name: 'signup' });
};

// 저장된 이메일 불러오기
onMounted(() => {
  const rememberedEmail = localStorage.getItem('rememberedEmail');
  if (rememberedEmail) {
    email.value = rememberedEmail;
    rememberMe.value = true;
  }
});
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-background"></div>
      
      <div class="login-content">
        <div class="logo-container">
          <img 
            src="@/assets/images/planova-small-logo.jpg"
            alt="PLANOVA 로고" 
            class="logo-image"
          />
        </div>
        
        <h1 class="login-title">
          프리미엄 AI 튜터와 함께<br>
          <span class="highlight">학습의 여정을 시작하세요!</span>
        </h1>
        
        <!-- 로그인 탭 메뉴 -->
        <div class="login-tabs">
          <button 
            @click="activeTab = 'email'" 
            :class="{ active: activeTab === 'email' }"
            class="tab-button"
          >
            이메일로 로그인
          </button>
          <button 
            @click="activeTab = 'kakao'" 
            :class="{ active: activeTab === 'kakao' }"
            class="tab-button"
          >
            카카오로 로그인
          </button>
        </div>
        
        <!-- 이메일 로그인 폼 -->
        <div v-if="activeTab === 'email'" class="tab-content email-form">
          <form @submit.prevent="emailLogin">
            <div class="form-group">
              <label for="email">이메일</label>
              <input 
                type="email" 
                id="email" 
                v-model="email" 
                placeholder="이메일 주소를 입력하세요"
                :class="{ 'input-error': email && !isEmailValid }"
                required
              />
              <small v-if="email && !isEmailValid" class="error-text">
                유효한 이메일 주소를 입력해주세요.
              </small>
            </div>
            
            <div class="form-group">
              <label for="password">비밀번호</label>
              <input 
                type="password" 
                id="password" 
                v-model="password" 
                placeholder="비밀번호를 입력하세요"
                :class="{ 'input-error': password && !isPasswordValid }"
                required
              />
              <small v-if="password && !isPasswordValid" class="error-text">
                비밀번호는 최소 6자 이상이어야 합니다.
              </small>
            </div>
            
            <div class="form-options">
              <div class="remember-me">
                <input type="checkbox" id="remember" v-model="rememberMe" />
                <label for="remember">이메일 기억하기</label>
              </div>
              <a href="#" class="forgot-password">비밀번호 찾기</a>
            </div>
            
            <button 
              type="submit" 
              class="login-button"
              :disabled="isLoading || (!isFormValid && (email || password))"
            >
              <span v-if="!isLoading">로그인</span>
              <div v-else class="button-spinner"></div>
            </button>
            
            <div v-if="emailLoginError" class="login-error">
              {{ emailLoginError }}
            </div>
            
            <div class="signup-link">
              계정이 없으신가요?<a href="#" @click.prevent="goToSignup">회원가입</a>
            </div>
          </form>
        </div>
        
        <!-- 카카오 로그인 -->
        <div v-if="activeTab === 'kakao'" class="tab-content">
          <div class="kakao-button-container">
            <img 
              src="@/assets/images/kakao_login_large_wide.png" 
              alt="카카오 로그인" 
              class="kakao-login-image" 
              @click="kakaoLogin"
              :class="{ 'disabled': isLoading || !debug.isInitialized }"
            />
            <div v-if="isLoading" class="loading-overlay">
              <div class="loading-spinner"></div>
              <span>로그인 중...</span>
            </div>
          </div>
        </div>
        
        <div class="divider">
          <span>PLANOVA만의 특별한 기능</span>
        </div>
        
        <div class="benefits">
          <div class="benefit-item">
            <div class="benefit-icon">
              <div class="icon-background">
                <span>🎓</span>
              </div>
            </div>
            <div class="benefit-text">맞춤형 학습 계획</div>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon">
              <div class="icon-background">
                <span>📊</span>
              </div>
            </div>
            <div class="benefit-text">학습 통계 분석</div>
          </div>
          <div class="benefit-item">
            <div class="benefit-icon">
              <div class="icon-background">
                <span>🤖</span>
              </div>
            </div>
            <div class="benefit-text">AI 튜터 서비스</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 20px;
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
}

.login-box {
  width: 100%;
  max-width: 480px;
  position: relative;
  background-color: white;
  border-radius: 24px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  animation: fadeIn 0.8s ease-out;
}

.login-background {
  position: absolute;
  top: 0;
  right: 0;
  width: 60%;
  height: 180px;
  background: linear-gradient(135deg, #ffb23f 0%, #ff6f00 100%);
  border-radius: 0 0 0 100px;
  opacity: 0.8;
  transform: translateY(-60%);
}

.login-content {
  position: relative;
  padding: 50px 40px;
  z-index: 1;
}

.logo-container {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 10px;
  margin-left: -10px;
}

.logo-image {
  width: 80px;
  height: auto;
  transition: transform 0.3s ease;
}

.logo-image:hover {
  transform: scale(1.05);
}

.login-title {
  text-align: left;
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 35px;
  color: #1a1a1a;
  line-height: 1.4;
  letter-spacing: -0.5px;
}

.highlight {
  position: relative;
  display: inline-block;
  color: #F37322;
  z-index: 1;
}

.highlight::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 30%;
  background-color: rgba(255, 156, 63, 0.2);
  z-index: -1;
  border-radius: 3px;
}

/* 로그인 탭 스타일 */
.login-tabs {
  display: flex;
  margin-bottom: 25px;
  border-bottom: 1px solid #e0e0e0;
}

.tab-button {
  flex: 1;
  background: none;
  border: none;
  padding: 12px 0;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.tab-button.active {
  color: #F37322;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #F37322;
}

.tab-content {
  margin-bottom: 30px;
}

/* 이메일 로그인 폼 스타일 */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.form-group input:focus {
  border-color: #F37322;
  box-shadow: 0 0 0 2px rgba(243, 115, 34, 0.1);
}

.input-error {
  border-color: #e53935 !important;
}

.error-text {
  color: #e53935;
  font-size: 12px;
  margin-top: 5px;
  display: block;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 13px;
}

.remember-me {
  display: flex;
  align-items: center;
}

.remember-me input {
  margin-right: 6px;
}

.forgot-password {
  color: #666;
  text-decoration: none;
  transition: color 0.3s;
}

.forgot-password:hover {
  color: #F37322;
  text-decoration: underline;
}

.login-button {
  width: 100%;
  padding: 14px;
  background-color: #F37322;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-button:hover:not(:disabled) {
  background-color: #e05e0a;
  transform: translateY(-2px);
}

.login-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
}

.button-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

.login-error {
  margin-top: 15px;
  padding: 10px;
  background-color: #ffebee;
  color: #c62828;
  border-radius: 6px;
  font-size: 14px;
  text-align: center;
}

.signup-link {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #666;
}

.signup-link a {
  color: #F37322;
  text-decoration: none;
  font-weight: 500;
}

.signup-link a:hover {
  text-decoration: underline;
}

/* 카카오 로그인 스타일 */
.kakao-button-container {
  position: relative;
  width: 100%;
  margin-bottom: 10px;
  transition: transform 0.3s ease;
}

.kakao-button-container:hover {
  transform: translateY(-3px);
}

.kakao-login-image {
  width: 100%;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.kakao-login-image:hover {
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.18);
}

.kakao-login-image.disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  font-weight: 600;
  color: #333;
  gap: 12px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(243, 115, 34, 0.3);
  border-radius: 50%;
  border-top-color: #F37322;
  animation: spin 1s linear infinite;
}

/* 구분선 및 하단 기능 스타일 */
.divider {
  position: relative;
  margin: 0 0 30px;
  text-align: center;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: #e0e0e0;
}

.divider span {
  position: relative;
  display: inline-block;
  padding: 0 15px;
  background-color: white;
  color: #666;
  font-size: 15px;
  font-weight: 500;
}

.benefits {
  display: flex;
  justify-content: space-between;
}

.benefit-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  padding: 0 8px;
}

.benefit-icon {
  margin-bottom: 12px;
}

.icon-background {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background-color: #fff4eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.icon-background:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(243, 115, 34, 0.15);
}

.benefit-text {
  text-align: center;
  font-size: 14px;
  color: #444;
  font-weight: 500;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .login-content {
    padding: 40px 25px;
  }
  
  .logo-image {
    width: 70px;
  }
  
  .login-title {
    font-size: 22px;
    margin-bottom: 25px;
  }
  
  .tab-button {
    font-size: 14px;
    padding: 10px 0;
  }
  
  .form-group input {
    padding: 10px;
  }
  
  .benefit-item {
    padding: 0 5px;
  }
  
  .icon-background {
    width: 45px;
    height: 45px;
    font-size: 20px;
  }
  
  .benefit-text {
    font-size: 12px;
  }
}
</style>