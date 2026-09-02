export function createMobileNavigationState ({ isMobile = false } = {}) {
  return {
    isMobile,
    isOpen: false,
    open () {
      if (this.isMobile) this.isOpen = true
    },
    close () {
      this.isOpen = false
    },
    routeChanged () {
      if (this.isMobile) this.isOpen = false
    },
    setViewport (nextIsMobile) {
      this.isMobile = nextIsMobile
      if (!nextIsMobile) this.isOpen = false
    }
  }
}
