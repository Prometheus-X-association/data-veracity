package hu.bme.mit.ftsrg.dva.util;

import java.util.List;

class JoinUtils {

  public static String join(List<String> source) {
    StringBuilder result = new StringBuilder();
    for (String s : source) {
      if (!result.isEmpty()) {
        result.append(" ");
      }
      result.append(s);
    }

    return result.toString();
  }
}
