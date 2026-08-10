<template>
  <header>
    <div class="brand-mark">DVA</div>
    <div>
      <h1>Data Veracity Assurance</h1>
      <p>Monitor attestations, verifications, and credentials</p>
    </div>
  </header>
</template>

<style scoped>
  header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 24px;
    min-height: 50px;
    background-color: #fff;
    border-bottom: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(15, 23, 42, .06);
  }

  .brand-mark {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: #0891b2;
    color: #fff;
    font-weight: 800;
  }

  header > div > h1 {
    color: #0f172a;
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
  }

  p {
    margin: 2px 0 0;
    color: #64748b;
    font-size: .85rem;
  }
</style>
