package com.example.demo.api

import com.example.demo.dto.UserTokenDTO
import com.example.demo.service.UserTokenService
import org.springframework.http.MediaType.APPLICATION_JSON_VALUE
import org.springframework.http.ResponseEntity
import org.springframework.http.ResponseEntity.ok
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController

@RestController
class TokenController (
    val userTokenService: UserTokenService
) {
    @GetMapping(
        value = ["/api/register"],
        produces = [APPLICATION_JSON_VALUE, APPLICATION_JSON_VALUE])
    fun getNewToken(): ResponseEntity<UserTokenDTO> {
        val token = userTokenService.getNewToken()
        return ok(UserTokenDTO(token))
    }
}