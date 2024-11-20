package hu.bme.mit.ftsrg.dva.util;

import java.util.List;

public class StringUtils {

    public static String join(List<String> source) {
        return JoinUtils.join(source);
    }

    public static List<String> split(String source) {
        return SplitUtils.split(source);
    }
}
