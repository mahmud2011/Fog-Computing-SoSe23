package com.example.demo.service

import com.example.demo.dto.ConfigDTO
import com.example.demo.dto.EdgeDataDTO
import com.example.demo.repository.ConfigRepository
import com.example.demo.repository.EdgeDataRepository
import org.springframework.messaging.simp.SimpMessagingTemplate
import org.springframework.stereotype.Service

@Service
class ConfigService(
    val configRepository: ConfigRepository,
    val edgeDataRepository: EdgeDataRepository,
    val simpMessagingTemplate: SimpMessagingTemplate
) {
    fun saveConfig(config: ConfigDTO): ConfigDTO {
        val edgeDataRecord = edgeDataRepository.findById(config.edgeId)
        if (edgeDataRecord.isPresent)
            config.id = configRepository.save(config.toConfigEntity(edgeDataRecord.get())).id

        return config
    }

    fun updateConfig(config: ConfigDTO): ConfigDTO {
        val configRecord = config.id?.let { configRepository.findById(it) }
        configRecord?.ifPresent {
            it.data = config.data
            val updatedRecord = configRepository.save(it)
            config.edgeId = updatedRecord.edgeData?.id!!
            config.data = updatedRecord.data!!
            simpMessagingTemplate.convertAndSend("/topic/config", config)
        }
        return config
    }

    fun getAllConfig(): List<ConfigDTO>? {
        return configRepository.findAll().map {
            return@map ConfigDTO(
                id = it.id,
                data = it.data!!,
                edgeId = it.edgeData?.id!!
            )
        }
    }
}