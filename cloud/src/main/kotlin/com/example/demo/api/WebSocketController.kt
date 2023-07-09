package com.example.demo.api

import com.example.demo.dto.ConfigDTO
import com.example.demo.dto.EdgeDataDTO
import org.springframework.messaging.handler.annotation.MessageMapping
import org.springframework.messaging.handler.annotation.SendTo
import org.springframework.stereotype.Controller


@Controller
class WebSocketController {
    @MessageMapping("/config")
    @SendTo("/topic/config")
    @Throws(Exception::class)
    fun sendConfig(config: ConfigDTO): ConfigDTO? {
        return config
    }

    @MessageMapping("/edge-data")
    @SendTo("/topic/edge-data")
    @Throws(Exception::class)
    fun sendEdgeData(edgeData: EdgeDataDTO): EdgeDataDTO? {
        return edgeData
    }
}