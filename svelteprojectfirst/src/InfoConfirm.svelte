<script>
  import { createEventDispatcher } from 'svelte';

  export let userInfo;

  const dispatch = createEventDispatcher();

  function handleBack() {
      dispatch('back');
  }

  function formatLabel(key) {
      const labels = {
          name: '성함',
          age: '연령',
          sex: '성별',
          weight: '몸무게',
          height: '키',
          sleepTime: '하루 수면시간',
          drink: '음주 여부',
          smoke: '흡연 여부',
          fatigue: '피로 여부',
          systolicBP: '수축기 혈압',
          diastolicBP: '이완기 혈압',
          heartRate: '심박수',
          walking: '하루 걸음 수',
          cholesterol: '콜레스테롤 과다 여부'
      };
      return labels[key] || key;
  }

  function formatValue(key, value) {
      if (value === null || value === undefined || value === '') {
          return '미입력';
      }
      if (key === 'sex') {
          return value === '남자' ? '남자' : '여자';
      }
      if (['drink', 'smoke', 'fatigue', 'cholesterol'].includes(key)) {
          return value === '예' ? '예' : '아니오';
      }
      if (key === 'weight') {
          return `${value} kg`;
      }
      if (key === 'height') {
          return `${value} cm`;
      }
      if (key === 'sleepTime') {
          return `${value} 시간`;
      }
      if (key === 'walking') {
          const walkingLabels = {
              10000: '매우 많이 걷는다',
              8000: '꽤 많이 걷는다',
              7000: '보통 걷는다',
              5600: '조금 걷는다',
              3000: '거의 걷지 않는다'
          };
          return `${walkingLabels[value]} (${value} 걸음)`;
      }
      return value;
  }
</script>

<div class="info-confirm">
  <h2>입력하신 정보가 맞나요?</h2>
  
  <div class="info-list">
      {#each Object.entries(userInfo) as [key, value]}
          <div class="info-item">
              <span class="label">{formatLabel(key)}:</span>
              <span class="value">{formatValue(key, value)}</span>
          </div>
      {/each}
  </div>

  <div class="navigation">
      <button on:click={handleBack}>돌아가기</button>
      <button on:click={() => alert('정보가 저장되었습니다.')}>확인</button>
  </div>
</div>

<style>
  .info-confirm {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
  }

  h2 {
      margin-bottom: 1em;
  }

  .info-list {
      text-align: left;
      margin-bottom: 1em;
  }

  .info-item {
      margin-bottom: 0.5em;
  }

  .label {
      font-weight: bold;
      margin-right: 0.5em;
  }

  .navigation {
      display: flex;
      justify-content: space-between;
      width: 100%;
      max-width: 300px;
  }
</style>
