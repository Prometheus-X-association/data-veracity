package hu.bme.mit.ftrsg.dva.app;

import hu.bme.mit.ftsrg.dva.util.StringUtils;

public class App {

  public static void main(String[] args) {
    var tokens = StringUtils.split(MessageUtils.getMessage());
    String result = StringUtils.join(tokens);
    System.out.println(result);
  }
}
