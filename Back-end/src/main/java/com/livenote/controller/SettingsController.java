package com.livenote.controller;

import com.livenote.dto.SetLanguageRequest;
import com.livenote.dto.SetPasswordRequest;
import com.livenote.dto.UserView;
import com.livenote.service.SettingsService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users/me")
@RequiredArgsConstructor
public class SettingsController {
    private final SettingsService settingsService;

    @GetMapping
    public ResponseEntity<UserView> getUser() {
        return ResponseEntity.ok(settingsService.getUser());
    }

    @PatchMapping("/language")
    public ResponseEntity<UserView> setLanguage(@Valid @RequestBody SetLanguageRequest request) {
        return ResponseEntity.ok(settingsService.setLanguage(request));
    }

    @PatchMapping("/password")
    public ResponseEntity<UserView> setPassword(@Valid @RequestBody SetPasswordRequest request) {
        return ResponseEntity.ok(settingsService.setPassword(request));
    }
}

