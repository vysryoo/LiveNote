package com.capstone.livenote;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class LivenoteApplication {

	public static void main(String[] args) {

        SpringApplication.run(LivenoteApplication.class, args);
	}

}
