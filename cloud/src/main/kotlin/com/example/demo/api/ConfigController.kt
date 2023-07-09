package com.example.demo.api

import com.example.demo.dto.ConfigDTO
import com.example.demo.service.ConfigService
import org.springframework.http.MediaType.ALL_VALUE
import org.springframework.http.MediaType.APPLICATION_JSON_VALUE
import org.springframework.http.ResponseEntity
import org.springframework.http.ResponseEntity.ok
import org.springframework.web.bind.annotation.*

@RestController
class ConfigController(
    val configService: ConfigService
) {
    @PostMapping(
        value = ["/api/config"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun persistConfig(
        @RequestBody config: ConfigDTO,
    ): ResponseEntity<Any> {
        return ok(configService.saveConfig(config))
    }

    @PatchMapping(
        value = ["/api/config"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun updateConfig(
        @RequestBody config: ConfigDTO,
    ): ResponseEntity<ConfigDTO> {
        return ok(configService.updateConfig(config))
    }

    @GetMapping(
        value = ["/api/configs"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun getAllConfig(): ResponseEntity<List<ConfigDTO>> {
        return ok(configService.getAllConfig())
    }
}