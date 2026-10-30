package com.capstone.livenote.lecture;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CreateLectureRequestDto {
    private String title;
    private String subject;
    private String sttLanguage;
}
