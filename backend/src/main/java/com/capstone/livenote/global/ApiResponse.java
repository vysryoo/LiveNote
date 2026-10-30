package com.capstone.livenote.global;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * REST API 응답 본문의 공통 형식 {@code {ok, data, message}}.
 *
 * @param <T> 응답 데이터 타입
 */
@Getter
@AllArgsConstructor
public class ApiResponse<T> {
    private boolean ok;
    private T data;
    private String message;

    /**
     * 데이터를 담은 성공 응답을 만든다.
     *
     * @param data 응답 데이터
     * @param <T> 응답 데이터 타입
     * @return 성공 응답
     */
    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(true, data, null);
    }

    /**
     * 데이터 없는 성공 응답을 만든다.
     *
     * @return 성공 응답
     */
    public static ApiResponse<Void> ok() {
        return new ApiResponse<>(true, null, null);
    }

    /**
     * 실패 응답을 만든다.
     *
     * @param msg 오류 메시지
     * @return 실패 응답
     */
    public static ApiResponse<Void> fail(String msg) {
        return new ApiResponse<>(false, null, msg);
    }
}

