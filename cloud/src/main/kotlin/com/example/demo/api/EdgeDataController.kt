package com.example.demo.api

import com.example.demo.dto.EdgeDataDTO
import com.example.demo.service.EdgeDataService
import com.example.demo.service.UserTokenService
import org.springframework.http.MediaType.ALL_VALUE
import org.springframework.http.MediaType.APPLICATION_JSON_VALUE
import org.springframework.http.ResponseEntity
import org.springframework.http.ResponseEntity.badRequest
import org.springframework.http.ResponseEntity.ok
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PatchMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class EdgeDataController(
    val edgeDataService: EdgeDataService,
    val userTokenService: UserTokenService
) {
    @PostMapping(
        value = ["/api/edge-data"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun persistConfig(
        @RequestBody edgeData: EdgeDataDTO,
    ): ResponseEntity<EdgeDataDTO> {
        return if (userTokenService.isUserTokenValid(edgeData.token)) {
            return ok(edgeDataService.saveEdgeData(edgeData))
        } else {
            badRequest().body(edgeData)
        }
    }

    @PatchMapping(
        value = ["/api/edge-data"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun updateConfig(
        @RequestBody edgeData: EdgeDataDTO,
    ): ResponseEntity<EdgeDataDTO> {
        return if (userTokenService.isUserTokenValid(edgeData.token)) {
            edgeDataService.updateEdgeData(edgeData)
            return ok(edgeData)
        } else {
            badRequest().body(edgeData)
        }
    }

    @GetMapping(
        value = ["/api/edge-data"],
        produces = [APPLICATION_JSON_VALUE, ALL_VALUE]
    )
    fun getAllEdgeData(): ResponseEntity<List<EdgeDataDTO>> {
            return ok(edgeDataService.getAllEdgeData())
    }
}