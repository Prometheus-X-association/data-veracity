import test from 'node:test'
import assert from 'node:assert/strict'
import { createMobileNavigationState } from '../dva-dashboard/src/utils/mobileNavigation.mjs'

test('opens and closes the mobile drawer', () => {
  const nav = createMobileNavigationState({ isMobile: true })
  nav.open()
  assert.equal(nav.isOpen, true)
  nav.close()
  assert.equal(nav.isOpen, false)
})

test('route changes close an open mobile drawer', () => {
  const nav = createMobileNavigationState({ isMobile: true })
  nav.open()
  nav.routeChanged()
  assert.equal(nav.isOpen, false)
})

test('desktop viewport changes close the drawer', () => {
  const nav = createMobileNavigationState({ isMobile: true })
  nav.open()
  nav.setViewport(false)
  assert.equal(nav.isOpen, false)
})
