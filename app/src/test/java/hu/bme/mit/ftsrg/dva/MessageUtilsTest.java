package hu.bme.mit.ftsrg.dva;

import static org.junit.jupiter.api.Assertions.assertEquals;

import hu.bme.mit.ftrsg.dva.app.MessageUtils;
import org.junit.jupiter.api.Test;

class MessageUtilsTest {
  @Test
  void testGetMessage() {
    assertEquals("Hello      World!", MessageUtils.getMessage());
  }
}
