package com.capstone.livenote.user;

public record SetPasswordRequest(String currentPassword, String newPassword) {}
