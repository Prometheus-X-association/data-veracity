<template>
  <div class="dashboard-wrapper">
    <h2 class="page-title">Dashboard | Data Veracity Assurance</h2>

    <!-- Issued Attestations -->
    <section class="section mb-5">
      <h4 class="section-title">Issued Attestations</h4>
      <div class="card-container">
        <div
          class="card-issued"
          v-for="att in issuedList"
          :key="att.id"
        >
          <div class="card-body">
            <!-- Single‐line header -->
            <h5 class="card-title mb-2">
              ID: {{ att.id }}
            </h5>            
            <div class="card-content-left">
              <p class="card-text"><strong class="metadata-label">Data ID:</strong> {{ att.dataItemId }}</p>
              <p class="card-text"><strong class="metadata-label">Contract:</strong> {{ att.contractId }}</p>
              <p class="card-text"><strong class="metadata-label">Issued At:</strong> {{ att.issuedAt }}</p>
              <p class="card-text mb-2">
                <strong class="metadata-label">Status:</strong>
                <span v-if="att.passed" class="badge badge-success">PASSED</span>
                <span v-else class="badge badge-danger">FAILED</span>
              </p>
              <hr class="divider" />
              <h6 class="card-subtitle">Evaluation Results:</h6>
              <ul class="results-list">
                <li v-for="(r, i) in att.evaluationResults" :key="i">
                  <span class="fw-semibold">{{ r.aspect }}:</span>
                  <span v-if="r.result === 'passed'" class="text-success fw-semibold">
                    {{ r.result }}
                  </span>
                  <span v-else class="text-danger fw-semibold">
                    {{ r.result }} ({{ r.reason }})
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Requested Attestations -->
    <section class="section">
      <h4 class="section-title">Requested Attestations</h4>
      <div class="card-container">
        <div
          class="card-issued"
          v-for="att in requestedList"
          :key="att.id"
        >
          <div class="card-body">
            <!-- Single‐line header -->
            <h5 class="card-title mb-2">
              ID: {{ att.id }}
            </h5>
            <div class="card-content-left">
              <p class="card-text"><strong class="metadata-label">Data ID:</strong> {{ att.dataItemId }}</p>
              <p class="card-text"><strong class="metadata-label">Contract:</strong> {{ att.contractId }}</p>
              <p class="card-text"><strong class="metadata-label">Requested At:</strong> {{ att.requestedAt }}</p>
              <p class="card-text mb-2"><strong class="metadata-label">Issued By:</strong> {{ att.issuerId }}</p>
              <p class="card-text mb-2">
                <strong class="metadata-label">Status:</strong>
                <span v-if="att.passed" class="badge badge-success">PASSED</span>
                <span v-else class="badge badge-danger">FAILED</span>
              </p>
              <hr class="divider" />
              <h6 class="card-subtitle">Evaluation Results:</h6>
              <ul class="results-list">
                <li v-for="(r, i) in att.evaluationResults" :key="i">
                  <span class="fw-semibold">{{ r.aspect }}:</span>
                  <span v-if="r.result === 'passed'" class="text-success fw-semibold">
                    {{ r.result }}
                  </span>
                  <span v-else class="text-danger fw-semibold">
                    {{ r.result }} ({{ r.reason }})
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  setup() {
    const issuedList = ref([])
    const requestedList = ref([])

    onMounted(async () => {
      try {
        const [issRes, reqRes] = await Promise.all([
          axios.get('/api/issued'),
          axios.get('/api/requested')
        ])
        issuedList.value = issRes.data
        requestedList.value = reqRes.data
      } catch (err) {
        console.error('Fetch error:', err)
      }
    })

    return { issuedList, requestedList }
  }
}
</script>

<style scoped>
.dashboard-wrapper {
  padding: 1rem 1.5rem;
}

.page-title {
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 1.75rem;
  font-weight: 500;
  color: #222;
}

/* Force exactly 4 columns */
.card-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

/* Common card styling */
.card-issued {
  background-color: #F0EAFB;
  border-radius: 0.75rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  transition: transform 0.1s, box-shadow 0.1s;
  display: flex;
  flex-direction: column;
}

.card-issued:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Remove border on requested cards; same as issued now */
.card-requested {
  /* identical styling to issued */
  background-color: #F0EAFB;
  border-radius: 0.75rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
  transition: transform 0.1s, box-shadow 0.1s;
  display: flex;
  flex-direction: column;
}

.card-requested:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Left-align all content */
.card-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  text-align: left;
  height: 100%;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.card-text {
  margin: 0.25rem 0;
  color: #444;
  font-size: 0.9rem;
}

.divider {
  border: none;
  border-top: 1px solid #DDD;
  margin: 0.75rem 0;
}

.card-subtitle {
  font-size: 0.95rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.results-list {
  list-style-type: disc;
  margin: 0;
  padding-left: 1.25rem;
  flex-grow: 1;
}

.results-list li {
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  color: #333;
}

.fw-semibold {
  font-weight: 600;
}

/* Add spacing after metadata labels */
.metadata-label {
  margin-right: 0.75rem;
}

/* Badge overrides */
.badge {
  padding: 0.25em 0.5em;
  font-size: 0.75rem;
  border-radius: 0.5rem;
  color: #fff;
}
.badge-success {
  background-color: #198754;
}
.badge-danger {
  background-color: #dc3545;
}
</style>
